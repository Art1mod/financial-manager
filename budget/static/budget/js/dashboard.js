// ==========================================
// 1. CONFIGURATION
// ==========================================
const currencySymbols = { 'CZK': 'Kč', 'USD': '$', 'EUR': '€' };

// ==========================================
// 2. SHARED RENDERERS (Centralized UI Logic)
// ==========================================

function switchView(panelId, tabButton) {
    document.querySelectorAll('.view-panel').forEach(p => p.classList.remove('panel-visible'));
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active-tab'));
    document.getElementById(panelId).classList.add('panel-visible');
    tabButton.classList.add('active-tab');
}

function refreshDashboardUI(data, symbol) {
    // 1. Update Financials
    document.getElementById('balance-display').innerText = `${data.metrics.current_balance.toFixed(2)} ${symbol}`;
    document.getElementById('income-display').innerText = `+ ${data.metrics.total_income.toFixed(2)} ${symbol}`;
    document.getElementById('expense-display').innerText = `- ${data.metrics.total_expense.toFixed(2)} ${symbol}`;

    // 2. Update Table
    document.getElementById('transaction-table-body').innerHTML = data.table_html;

    // 3. Sync Achievements
    const recentWrapper = document.getElementById('dynamic-achievements-wrapper');
    if (recentWrapper && data.recent_html) recentWrapper.innerHTML = data.recent_html;
    
    const allView = document.getElementById('achievements-view');
    if (allView && data.all_html) allView.innerHTML = data.all_html;
}

// Logic to populate category dropdowns dynamically
function updateCategoryOptions(typeField, categoryField) {
    const selectedType = typeField.value;
    const currentCategory = categoryField.value;
    
    categoryField.innerHTML = '<option value="">---------</option>';
    
    if (selectedType) {
        const options = (selectedType === 'INCOME') ? incomeCats : expenseCats;
        options.forEach(cat => {
            const opt = document.createElement('option');
            opt.value = cat[0];
            opt.textContent = cat[1];
            if (cat[0] === currentCategory) opt.selected = true;
            categoryField.appendChild(opt);
        });
    }
}

// ==========================================
// 3. API ACTIONS
// ==========================================

function deleteTransaction(transactionId) {
    if (!confirm('Opravdu chcete tuto transakci smazat?')) return;

    const currency = document.getElementById('id_currency').value;
    fetch(`/delete-transaction/${transactionId}/?currency=${currency}`, {
        method: "POST",
        headers: { "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value }
    })
    .then(r => r.json())
    .then(data => data.status === 'success' ? refreshDashboardUI(data, currencySymbols[currency]) : alert('Chyba při mazání.'));
}

function openEditModal(transactionId) {
    const modal = document.getElementById('edit-modal');
    fetch(`/get-transaction/${transactionId}/`)
    .then(r => r.json())
    .then(data => {
        document.getElementById('edit-transaction-id').value = transactionId;
        document.getElementById('edit-form-container').innerHTML = data.form_html;
        
        modal.style.display = 'block';
        modal.classList.add('show');

        // Initialize category logic
        const container = document.getElementById('edit-form-container');
        const typeField = container.querySelector('select[name="transaction_type"]');
        const categoryField = container.querySelector('select[name="category"]');
        
        typeField.addEventListener('change', () => updateCategoryOptions(typeField, categoryField));
        updateCategoryOptions(typeField, categoryField);
    });
}

function closeEditModal() {
    const modal = document.getElementById('edit-modal');
    modal.classList.remove('show');
    modal.style.display = 'none';
}

// ==========================================
// 4. INITIALIZATION
// ==========================================

document.addEventListener('DOMContentLoaded', function() {
    // Description Counter
    const descField = document.querySelector('textarea[name="description"]');
    const counter = document.getElementById('char-counter');
    if (descField && counter) {
        descField.addEventListener('input', () => {
            const len = descField.value.length;
            counter.innerText = `${len} / ${descField.getAttribute('data-max-length')} znaků`;
            counter.style.color = (len >= 255) ? '#dc2626' : '#7f8c8d';
        });
    }

    // Main Transaction Form Setup
    const mainForm = document.getElementById('transaction-form');
    const typeField = document.querySelector('select[name="transaction_type"]');
    const categoryField = document.querySelector('select[name="category"]');

    if (typeField && categoryField) {
        typeField.addEventListener('change', () => updateCategoryOptions(typeField, categoryField));
        updateCategoryOptions(typeField, categoryField);
    }

    mainForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const currency = document.getElementById('id_currency').value;
        const formData = new FormData(this);
        formData.append('dashboard_currency', currency);

        fetch(DjangoUrls.addTransaction, {
            method: "POST",
            body: formData,
            headers: { "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value }
        })
        .then(r => r.json())
        .then(data => {
            if (data.status === 'success') {
                refreshDashboardUI(data, currencySymbols[currency]);
                mainForm.reset();
            } else { alert('Chyba: ' + JSON.stringify(data.errors)); }
        });
    });

    // Currency Switcher
    document.getElementById('id_currency').addEventListener('change', function() {
        const currency = this.value;
        fetch(`${DjangoUrls.changeCurrency}?currency=${currency}`)
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') {
                    refreshDashboardUI(data, currencySymbols[currency]);
                    const url = new URL(window.location);
                    url.searchParams.set('currency', currency);
                    window.history.pushState({}, '', url);
                }
            });
    });

    // Edit Modal Form Submit
    document.getElementById('edit-transaction-form').addEventListener('submit', function(e) {
        e.preventDefault();
        const id = document.getElementById('edit-transaction-id').value;
        const currency = document.getElementById('id_currency').value;
        const formData = new FormData(this);
        formData.append('dashboard_currency', currency);

        fetch(`/update-transaction/${id}/`, {
            method: "POST",
            body: formData,
            headers: { "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value }
        })
        .then(r => r.json())
        .then(data => {
            if (data.status === 'success') {
                refreshDashboardUI(data, currencySymbols[currency]);
                closeEditModal();
            } else { alert('Chyba: ' + JSON.stringify(data.errors)); }
        });
    });
});