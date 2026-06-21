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