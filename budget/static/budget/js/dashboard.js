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
    document.getElementById('balance-display').innerText = `${metrics.current_balance} ${symbol}`;
    document.getElementById('income-display').innerText = `+ ${metrics.total_income} ${symbol}`;
    document.getElementById('expense-display').innerText = `- ${metrics.total_expense} ${symbol}`;
}

function prependTransactionRowUI(transaction) {
    const tbody = document.getElementById('transaction-table-body');
    const txSymbol = currencySymbols[transaction.currency] || '';
    const typeLabel = transaction.type === 'INCOME' ? '<span class="income">Příjem</span>' : '<span class="expense">Výdaj</span>';
    
    // Clear the "No transactions yet" message if it exists
    if (tbody.rows.length === 1 && tbody.rows[0].cells.length === 1) {
        tbody.innerHTML = '';
    }

    const newRow = `
        <tr>
            <td>${transaction.date}</td>
            <td>${typeLabel}</td>
            <td>${transaction.amount} ${txSymbol}</td>
            <td>${transaction.category}</td>
            <td>${transaction.description}</td>
        </tr>
    `;
    tbody.insertAdjacentHTML('afterbegin', newRow);
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

// ==========================================
// 3. EVENT LISTENERS (The "Input" Handlers)
// ==========================================

// Handle Currency Dropdown Change
document.getElementById('id_currency').addEventListener('change', function() {
    const selectedCurrency = this.value;
    const symbol = currencySymbols[selectedCurrency] || '';

    // Look here! Using DjangoUrls.changeCurrency
    fetch(`${DjangoUrls.changeCurrency}?currency=${selectedCurrency}`)
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            updateFinancialMetricsUI(data.metrics, symbol);
            
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
            prependTransactionRowUI(data.transaction);
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