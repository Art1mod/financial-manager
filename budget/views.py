# budget/views.py


# Django Imports
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.timezone import localtime

# Local App Imports
from .models import Transaction
from .forms import TransactionForm
from achievements.models import Achievement, UserAchievement
from .services import calculate_user_metrics

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

@login_required
def dashboard(request):
    selected_currency = request.GET.get('currency', 'CZK')
    if selected_currency not in ['CZK', 'USD', 'EUR']:
        selected_currency = 'CZK'

    user_transactions = Transaction.objects.filter(user=request.user).order_by('-date')
    metrics = calculate_user_metrics(request.user, selected_currency)

    # --- ACHIEVEMENT SUBSYSTEM ---
    all_achievements = Achievement.objects.all()
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
    return render(request, 'budget/dashboard.html', context)


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
