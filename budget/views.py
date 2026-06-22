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
from django.template import Template, Context
from django.db import transaction

# Local App Imports
from .models import Transaction
from .forms import TransactionForm
from achievements.models import UserAchievement
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

    recent_achievements = UserAchievement.objects.filter(
        user=request.user
    ).order_by('-date_unlocked')[:3]

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
        'recent_achievements': recent_achievements,
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
            
            with transaction.atomic():
                new_transaction = form.save(commit=False)
                new_transaction.user = request.user
                new_transaction.save()
            
            
            dashboard_currency = request.POST.get('dashboard_currency', 'CZK')
            metrics = calculate_user_metrics(request.user, dashboard_currency)
            user_transactions = get_annotated_transactions(request.user, dashboard_currency)


            table_html = render_to_string('budget/partials/transaction_table.html', {
                'transactions': user_transactions,
                'selected_currency': dashboard_currency
            })

            recent_achievements = UserAchievement.objects.filter(
                user=request.user
            ).order_by('-date_unlocked')[:3]

            recent_html = render_to_string(
                'achievements/recent_achievements_widget.html', 
                {'recent_achievements': recent_achievements}
            )
            
            template = Template("{% load gamification_tags %}{% render_user_achievements user %}")
            all_html = template.render(Context({'user': request.user}))

            return JsonResponse({
                'status': 'success',
                'table_html': table_html, 
                'recent_html': recent_html,
                'all_html': all_html,
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
    
    recent_achievements = UserAchievement.objects.filter(
        user=request.user
    ).order_by('-date_unlocked')[:3]

    recent_html = render_to_string(
        'achievements/recent_achievements_widget.html', 
        {'recent_achievements': recent_achievements}
    )
            
    template = Template("{% load gamification_tags %}{% render_user_achievements user %}")
    all_html = template.render(Context({'user': request.user}))

    return JsonResponse({
        'status': 'success',
        'table_html': table_html, 
        'recent_html': recent_html,
        'all_html': all_html,
        'metrics': {
            'total_income': float(metrics['total_income']),
            'total_expense': float(metrics['total_expense']),
            'current_balance': float(metrics['current_balance']),
        }
    })

@login_required
def get_transaction_details(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    form = TransactionForm(instance=transaction)
    form_html = render_to_string('budget/partials/edit_form.html', {'form': form})
    return JsonResponse({'form_html': form_html})

@login_required
def update_transaction_ajax(request, transaction_id):
    transaction_obj = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction_obj)
        if form.is_valid():
            
            with transaction.atomic():
                form.save()
            
            dashboard_currency = request.POST.get('dashboard_currency', 'CZK')
            metrics = calculate_user_metrics(request.user, dashboard_currency)
            user_transactions = get_annotated_transactions(request.user, dashboard_currency)
            
            table_html = render_to_string('budget/partials/transaction_table.html', {
                'transactions': user_transactions,
                'selected_currency': dashboard_currency
            })
            
            recent_achievements = UserAchievement.objects.filter(
                user=request.user
            ).order_by('-date_unlocked')[:3]

            recent_html = render_to_string(
                'achievements/recent_achievements_widget.html', 
                {'recent_achievements': recent_achievements}
            )
            
            template = Template("{% load gamification_tags %}{% render_user_achievements user %}")
            all_html = template.render(Context({'user': request.user}))

            return JsonResponse({
                'status': 'success',
                'table_html': table_html, 
                'recent_html': recent_html,
                'all_html': all_html,
                'metrics': {
                    'total_income': float(metrics['total_income']),
                    'total_expense': float(metrics['total_expense']),
                    'current_balance': float(metrics['current_balance']),
                }
            })
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)