# budget/views.py


# Django Imports
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.timezone import localtime
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

# Local App Imports
from .models import Transaction
from .forms import TransactionForm
from .services import calculate_user_metrics, get_annotated_transactions

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

    user_transactions = get_annotated_transactions(request.user, selected_currency)
    metrics = calculate_user_metrics(request.user, selected_currency)

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
        'INCOME_CATEGORIES': Transaction.INCOME_CATEGORIES,
        'EXPENSE_CATEGORIES': Transaction.EXPENSE_CATEGORIES,
    }
    return render(request, 'budget/dashboard.html', context)


@login_required
def change_currency_ajax(request):
    target_currency = request.GET.get('currency', 'CZK')
    if target_currency not in ['CZK', 'USD', 'EUR']:
        target_currency = 'CZK'
        
    metrics = calculate_user_metrics(request.user, target_currency)
    user_transactions = get_annotated_transactions(request.user, target_currency)
    
    table_html = render_to_string('budget/partials/transaction_table.html', {
        'transactions': user_transactions,
        'selected_currency': target_currency
    })
    
    return JsonResponse({
        'status': 'success',
        'metrics': {
            'total_income': float(metrics['total_income']),
            'total_expense': float(metrics['total_expense']),
            'current_balance': float(metrics['current_balance']),
        },
        'table_html': table_html 
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
            user_transactions = get_annotated_transactions(request.user, dashboard_currency)

            table_html = render_to_string('budget/partials/transaction_table.html', {
                'transactions': user_transactions,
                'selected_currency': dashboard_currency
            })

            return JsonResponse({
                'status': 'success',
                'table_html': table_html, 
                'metrics': {
                    'total_income': float(metrics['total_income']),
                    'total_expense': float(metrics['total_expense']),
                    'current_balance': float(metrics['current_balance']),
                }
            })
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@require_POST
@login_required
def delete_transaction_ajax(request, transaction_id):
    
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    transaction.delete()
    
    dashboard_currency = request.GET.get('currency', 'CZK')
    metrics = calculate_user_metrics(request.user, dashboard_currency)
    user_transactions = get_annotated_transactions(request.user, dashboard_currency)
    
    table_html = render_to_string('budget/partials/transaction_table.html', {
        'transactions': user_transactions,
        'selected_currency': dashboard_currency
    })
    
    return JsonResponse({
        'status': 'success',
        'table_html': table_html,
        'metrics': {
            'total_income': float(metrics['total_income']),
            'total_expense': float(metrics['total_expense']),
            'current_balance': float(metrics['current_balance']),
        }
    })