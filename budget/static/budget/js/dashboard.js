// ==========================================
// 1. CONFIGURATION & STATE
// ==========================================
const currencySymbols = { 'CZK': 'Kč', 'USD': '$', 'EUR': '€' };

// ==========================================
// 2. UI UPDATER FUNCTIONS (The "Render" Loop)
// ==========================================
function switchView(panelId, tabButton) {
    document.querySelectorAll('.view-panel').forEach(p => p.classList.remove('panel-visible'));
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active-tab'));
    document.getElementById(panelId).classList.add('panel-visible');
    tabButton.classList.add('active-tab');
}

function updateFinancialMetricsUI(metrics, symbol) {
    document.getElementById('balance-display').innerText = `${metrics.current_balance.toFixed(2)} ${symbol}`;
    document.getElementById('income-display').innerText = `+ ${metrics.total_income.toFixed(2)} ${symbol}`;
    document.getElementById('expense-display').innerText = `- ${metrics.total_expense.toFixed(2)} ${symbol}`;
}

function refreshAchievementsUI() {
    // Look here! We use the URL from the HTML Bridge
    fetch(DjangoUrls.getAchievements)
    .then(response => response.json())
    .then(achData => {
        const achievementsView = document.getElementById('achievements-view');
        const recentBanner = document.getElementById('recent-achievements-container');
        
        if (achievementsView) achievementsView.innerHTML = achData.all_html;
        if (recentBanner) recentBanner.outerHTML = achData.recent_html;
    })
    .catch(err => console.error("Error fetching achievements:", err));
}

function deleteTransaction(transactionId) {
    if (!confirm('Opravdu chcete tuto transakci smazat?')) return;

    const currency = document.getElementById('id_currency').value;
    const symbol = currencySymbols[currency] || '';

    fetch(`/delete-transaction/${transactionId}/?currency=${currency}`, {
        method: "POST",
        headers: { 
            "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value 
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            updateFinancialMetricsUI(data.metrics, symbol);
            document.getElementById('transaction-table-body').innerHTML = data.table_html;
        } else {
            alert('Chyba při mazání.');
        }
    });
}

function enableEdit(cell, transactionId, field) {
    const currentValue = cell.innerText;
    cell.innerHTML = `<input type="text" value="${currentValue}" onblur="saveEdit(this, ${transactionId}, '${field}')">`;
    cell.querySelector('input').focus();
}

function saveEdit(input, transactionId, field) {
    const newValue = input.value;
    // AJAX call to the edit_transaction_ajax view
    // After success: update metrics and reload table HTML
}

function openEditModal(transactionId) {
    const modal = document.getElementById('edit-modal');
    const container = document.getElementById('edit-form-container');

    fetch(`/get-transaction/${transactionId}/`)
    .then(response => response.json())
    .then(data => {
        document.getElementById('edit-transaction-id').value = transactionId;
        container.innerHTML = data.form_html;
        
        // Ensure modal is visible
        modal.style.display = 'block';
        modal.classList.add('show');

        // --- Smart Category logic inside modal ---
        const typeField = container.querySelector('select[name="transaction_type"]');
        const categoryField = container.querySelector('select[name="category"]');

        function updateModalCategories() {
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

        updateModalCategories();
        typeField.addEventListener('change', updateModalCategories);
    });
}

function closeEditModal() {
    const modal = document.getElementById('edit-modal');
    modal.classList.remove('show');
    modal.style.display = 'none';
}

document.addEventListener('DOMContentLoaded', function() {
    const descField = document.querySelector('textarea[name="description"]');
    const counter = document.getElementById('char-counter');

    if (descField && counter) {
        const limit = descField.getAttribute('data-max-length') || 255;
        
        descField.addEventListener('input', function() {
            const currentLength = descField.value.length;
            counter.innerText = `${currentLength} / ${limit} znaků`;
            
            // Optional: red color for nearing limit
            counter.style.color = (currentLength >= limit) ? '#dc2626' : '#7f8c8d';
        });
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const typeField = document.querySelector('select[name="transaction_type"]');
    const categoryField = document.querySelector('select[name="category"]');

    function updateCategories() {
        const selectedType = typeField.value; 
        
        // Save the current selection if we're just refreshing
        const currentCategory = categoryField.value;
        
        // Clear current options
        categoryField.innerHTML = '<option value="">---------</option>';
        
        // Populate new options
        if (selectedType) {
            const options = (selectedType === 'INCOME') ? incomeCats : expenseCats;
            
            options.forEach(cat => {
                const opt = document.createElement('option');
                opt.value = cat[0]; 
                opt.textContent = cat[1];
                // Re-select if it matches the previous value
                if (cat[0] === currentCategory) opt.selected = true;
                categoryField.appendChild(opt);
            });
        }
    }

    if (typeField && categoryField) {
        // Run on load to set initial state
        updateCategories();
        
        // Run on change
        typeField.addEventListener('change', updateCategories);
    }
});

document.getElementById('edit-transaction-form').addEventListener('submit', function(e) {
    e.preventDefault();
    const transactionId = document.getElementById('edit-transaction-id').value;
    const formData = new FormData(this);
    const activeCurrency = document.getElementById('id_currency').value;
    
    formData.append('dashboard_currency', activeCurrency);

    fetch(`/update-transaction/${transactionId}/`, {
        method: "POST",
        body: formData,
        headers: { "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            document.getElementById('transaction-table-body').innerHTML = data.table_html;
            updateFinancialMetricsUI(data.metrics, currencySymbols[activeCurrency]);
            closeEditModal();
        } else {
            alert('Chyba: ' + JSON.stringify(data.errors));
        }
    });
});

// ==========================================
// 3. EVENT LISTENERS (The "Input" Handlers)
// ==========================================

// Handle Currency Dropdown Change
document.getElementById('id_currency').addEventListener('change', function() {
    const selectedCurrency = this.value;
    const symbol = currencySymbols[selectedCurrency] || '';

    fetch(`${DjangoUrls.changeCurrency}?currency=${selectedCurrency}`)
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            updateFinancialMetricsUI(data.metrics, symbol);

            document.getElementById('transaction-table-body').innerHTML = data.table_html;
            
            // Update URL silently without refreshing
            const url = new URL(window.location);
            url.searchParams.set('currency', selectedCurrency);
            window.history.pushState({}, '', url);
        }
    });
});

// Handle Transaction Form Submission
document.getElementById('transaction-form').addEventListener('submit', function(e) {
    e.preventDefault();

    const form = this;
    const formData = new FormData(form);
    const activeDashboardCurrency = document.getElementById('id_currency').value;
    const dashboardSymbol = currencySymbols[activeDashboardCurrency] || '';
    
    formData.append('dashboard_currency', activeDashboardCurrency);

    // Look here! Using DjangoUrls.addTransaction
    fetch(DjangoUrls.addTransaction, {
        method: "POST",
        body: formData,
        headers: { "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            updateFinancialMetricsUI(data.metrics, dashboardSymbol);
            document.getElementById('transaction-table-body').innerHTML = data.table_html;
            refreshAchievementsUI();
            form.reset();
        } else {
            alert('Chyba při ukládání transakce: ' + JSON.stringify(data.errors));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Něco se pokazilo na serverové vrstvě.');
    });
});