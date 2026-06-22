# budget/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.template import Template, Context
from django.db import transaction

# Local App Imports
from .models import Transaction
from .forms import TransactionForm
from achievements.models import UserAchievement
from .services import calculate_user_metrics, get_annotated_transactions


def get_dashboard_context_json(user, dashboard_currency):
    """
    Centralized helper to package all dashboard dynamic components.
    Ensures consistency across Add, Delete, and Update AJAX actions.
    """
    metrics = calculate_user_metrics(user, dashboard_currency)
    user_transactions = get_annotated_transactions(user, dashboard_currency)
    
    # Render table
    table_html = render_to_string('budget/partials/transaction_table.html', {
        'transactions': user_transactions,
        'selected_currency': dashboard_currency
    })
    
    # Render achievements
    recent_achievements = UserAchievement.objects.filter(user=user).order_by('-date_unlocked')[:3]
    recent_html = render_to_string('achievements/recent_achievements_widget.html', {'recent_achievements': recent_achievements})
    
    template = Template("{% load gamification_tags %}{% render_user_achievements user %}")
    all_html = template.render(Context({'user': user}))
    
    return {
        'status': 'success',
        'table_html': table_html,
        'recent_html': recent_html,
        'all_html': all_html,
        'metrics': {
            'total_income': float(metrics['total_income']),
            'total_expense': float(metrics['total_expense']),
            'current_balance': float(metrics['current_balance']),
        }
    }

def register(request):
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
    currency = request.GET.get('currency', 'CZK')
    currency = currency if currency in ['CZK', 'USD', 'EUR'] else 'CZK'

    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            tx = form.save(commit=False)
            tx.user = request.user
            tx.save()
            return redirect(f"/dashboard/?currency={currency}")
    else:
        form = TransactionForm()

    context = {
        'transactions': get_annotated_transactions(request.user, currency),
        **calculate_user_metrics(request.user, currency),
        'selected_currency': currency,
        'form': form,
        'INCOME_CATEGORIES': Transaction.INCOME_CATEGORIES,
        'EXPENSE_CATEGORIES': Transaction.EXPENSE_CATEGORIES,
        'recent_achievements': UserAchievement.objects.filter(user=request.user).order_by('-date_unlocked')[:3],
    }
    return render(request, 'budget/dashboard.html', context)

@login_required
def change_currency_ajax(request):
    currency = request.GET.get('currency', 'CZK')
    return JsonResponse(get_dashboard_context_json(request.user, currency))

@login_required
def add_transaction_ajax(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                new_tx = form.save(commit=False)
                new_tx.user = request.user
                new_tx.save()
            currency = request.POST.get('dashboard_currency', 'CZK')
            return JsonResponse(get_dashboard_context_json(request.user, currency))
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    return JsonResponse({'status': 'error'}, status=400)

@require_POST
@login_required
def delete_transaction_ajax(request, transaction_id):
    tx = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    tx.delete()
    currency = request.GET.get('currency', 'CZK')
    return JsonResponse(get_dashboard_context_json(request.user, currency))

@login_required
def get_transaction_details(request, transaction_id):
    tx = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    form = TransactionForm(instance=tx)
    form_html = render_to_string('budget/partials/edit_form.html', {'form': form})
    return JsonResponse({'form_html': form_html})

@login_required
def update_transaction_ajax(request, transaction_id):
    tx_obj = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=tx_obj)
        if form.is_valid():
            with transaction.atomic():
                form.save()
            currency = request.POST.get('dashboard_currency', 'CZK')
            return JsonResponse(get_dashboard_context_json(request.user, currency))
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    return JsonResponse({'status': 'error'}, status=400)