# budget/services.py

import urllib.request
import json
from decimal import Decimal
from django.core.cache import cache
from .models import Transaction


def calculate_user_metrics(user, target_currency):
    """Converts user transactions dynamically using live ČNB exchange values."""
    transactions = Transaction.objects.filter(user=user)
    total_income = Decimal('0.0')   
    total_expense = Decimal('0.0')  
    
    live_rates = get_live_rates()
    
    # Convert target rate to Decimal
    target_rate = Decimal(str(live_rates.get(target_currency, 1.0)))
    
    for tx in transactions:
        # Convert source rate to Decimal
        source_rate = Decimal(str(live_rates.get(tx.currency, 1.0)))
        
        # 1. Convert source currency to base (CZK) safely
        amount_in_czk = tx.amount * source_rate
        
        # 2. Convert from CZK to dashboard's target view currency
        amount_in_target = amount_in_czk / target_rate
        
        if tx.transaction_type == 'INCOME':
            total_income += amount_in_target
        elif tx.transaction_type == 'EXPENSE':
            total_expense += amount_in_target
            
    return {
        'total_income': round(total_income, 2),
        'total_expense': round(total_expense, 2),
        'current_balance': round(total_income - total_expense, 2),
    }


def get_live_rates():
    """
    Fetches real-time exchange rates from ČNB and caches them in RAM 
    for 24 hours to prevent API spamming and speed up page loads.
    """
    # 1. Check if we already downloaded the rates recently
    cached_rates = cache.get('cnb_live_rates')
    if cached_rates:
        return cached_rates # Return instantly from RAM!

    # Safe default fallback rates if network drops
    rates = {'CZK': 1.0, 'USD': 23.5, 'EUR': 25.2}
    
    try:
        url = "https://api.cnb.cz/cnbapi/exrates/daily"
        req = urllib.request.Request(url, headers={'Accept': 'application/json'})
        
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            for item in data.get('rates', []):
                code = item.get('currencyCode')
                rate = item.get('rate')
                amount = item.get('amount', 1)
                
                if code in ['USD', 'EUR']:
                    rates[code] = float(rate) / float(amount)
                    
        # 2. Save the successful result to the Cache for 24 hours
        cache.set('cnb_live_rates', rates, 86400)
        print("✅ Successfully fetched and cached new ČNB rates!")
        
    except Exception as e:
        print(f"⚠️ ČNB API Fallback triggered: {e}")
        
    return rates



