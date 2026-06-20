import urllib.request
import json
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Transaction, Achievement, UserAchievement
from .forms import TransactionForm
from decimal import Decimal
from django.utils.timezone import localtime

def register(request):
    """Handles new user registrations."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def get_live_rates():
    """
    Fetches real-time exchange rates directly from the Czech National Bank (ČNB).
    Returns a safe fallback dictionary if the API is unreachable.
    """
    # Safe default fallback rates if network drops
    rates = {'CZK': 1.0, 'USD': 23.5, 'EUR': 25.2}
    try:
        url = "https://api.cnb.cz/cnbapi/exrates/daily/current"
        req = urllib.request.Request(url, headers={'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            for item in data.get('rates', []):
                code = item.get('currencyCode')
                rate = item.get('rate')
                amount = item.get('amount', 1)
                if code in ['USD', 'EUR']:
                    rates[code] = float(rate) / float(amount)
    except Exception as e:
        print(f"⚠️ ČNB API Fallback triggered: {e}")
    return rates

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

@login_required
def dashboard(request):
    selected_currency = request.GET.get('currency', 'CZK')
    if selected_currency not in ['CZK', 'USD', 'EUR']:
        selected_currency = 'CZK'

    user_transactions = Transaction.objects.filter(user=request.user).order_by('-date')
    metrics = calculate_user_metrics(request.user, selected_currency)

    # --- ACHIEVEMENT SUBSYSTEM ---
    all_achievements = Achievement.objects.all()
    check_and_assign_achievements(request.user)
    unlocked_badges = UserAchievement.objects.filter(user=request.user).values_list('achievement__badge_code', flat=True)
    
    achievements_context = []
    for ach in all_achievements:
        achievements_context.append({
            'title': ach.title,
            'desc': ach.description,
            'unlocked': ach.badge_code in unlocked_badges
        })

    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            return redirect(f"/dashboard/?currency={selected_currency}")
    else:
        form = TransactionForm()

    context = {
        'transactions': user_transactions,
        'total_income': metrics['total_income'],
        'total_expense': metrics['total_expense'],
        'current_balance': metrics['current_balance'],
        'selected_currency': selected_currency,
        'form': form,
        'achievements': achievements_context,
    }
    return render(request, 'dashboard.html', context)

@login_required
def change_currency_ajax(request):
    target_currency = request.GET.get('currency', 'CZK')
    if target_currency not in ['CZK', 'USD', 'EUR']:
        target_currency = 'CZK'
        
    metrics = calculate_user_metrics(request.user, target_currency)
    return JsonResponse({
        'status': 'success',
        'metrics': {
            'total_income': float(metrics['total_income']),
            'total_expense': float(metrics['total_expense']),
            'current_balance': float(metrics['current_balance']),
        }
    })

@login_required
def add_transaction_ajax(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            
            check_and_assign_achievements(request.user)
            
            dashboard_currency = request.POST.get('dashboard_currency', 'CZK')
            metrics = calculate_user_metrics(request.user, dashboard_currency)

            all_achievements = Achievement.objects.all()
            unlocked_badges = UserAchievement.objects.filter(user=request.user).values_list('achievement__badge_code', flat=True)

            achievements_ajax = []
            for ach in all_achievements:
                achievements_ajax.append({
                    'title': ach.title,
                    'desc': ach.description,  
                    'unlocked': ach.badge_code in unlocked_badges
                })

            return JsonResponse({
                'status': 'success',
                'transaction': {
                    'date': localtime(transaction.date).strftime('%d. %m. %Y') if transaction.date else '',
                    'type': transaction.transaction_type,
                    'amount': str(transaction.amount),
                    'currency': transaction.currency,
                    'category': transaction.get_category_display(),
                    'description': transaction.description or '',
                },
                'metrics': {
                    'total_income': float(metrics['total_income']),
                    'total_expense': float(metrics['total_expense']),
                    'current_balance': float(metrics['current_balance']),
                },
                'achievements': achievements_ajax
            })
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

def check_and_assign_achievements(user):
    """Dynamically checks conditions and unlocks user achievements."""
    czk_metrics = calculate_user_metrics(user, 'CZK')
    czk_balance = czk_metrics['current_balance']
    user_txs = Transaction.objects.filter(user=user)
    
    # 🏆 Milestone 1: První krok (Balance over 1000 Kč)
    if czk_balance > 1000:
        achievement = Achievement.objects.filter(badge_code='first_1000').first() # 'first_1000' must match  the badge_code in Django Admin
        if achievement:
            UserAchievement.objects.get_or_create(user=user, achievement=achievement)

    # 🏆 Milestone 2: Ranní ptáče (Transaction created before 9:00 AM local time)
    for tx in user_txs:
        if tx.date:
            local_time = localtime(tx.date)
            if local_time.hour < 24:
                achievement = Achievement.objects.filter(badge_code='first_of_day').first() # 'first_of_day' must match  the badge_code in Django Admin
                if achievement:
                    UserAchievement.objects.get_or_create(user=user, achievement=achievement)
                break
            
    # 🏆 Milestone 3: Finanční veterán (At least 10 transactions)
    if user_txs.count() >= 10:
        achievement = Achievement.objects.filter(badge_code='10_trans').first() # '10_trans' must match  the badge_code in Django Admin
        if achievement:
            UserAchievement.objects.get_or_create(user=user, achievement=achievement)