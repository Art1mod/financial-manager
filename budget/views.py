from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .models import Transaction
from .forms import TransactionForm
from django.http import JsonResponse
from django.utils.formats import date_format

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save() # Saves the new user into the SQLite DB
            login(request, user) # Automatically logs them in right after signing up
            return redirect('dashboard') # We will create the dashboard view later!
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required # Prevents unauthenticated guests from peaking at this page!
def dashboard(request):
    # --- DATA ISOLATION ENGINE ---
    # query ONLY transactions belonging exclusively to the logged-in user
    user_transactions = Transaction.objects.filter(user=request.user).order_by('-date')

    # --- FINANCIAL MATH ---
    total_income = 0
    total_expense = 0

    for tx in user_transactions:
        if tx.transaction_type == 'INCOME':
            total_income += tx.amount
        elif tx.transaction_type == 'EXPENSE':
            total_expense += tx.amount

    current_balance = total_income - total_expense

    # --- ACHIEVEMENT SUBSYSTEM ---
    achievements = [
        {
            'title': 'První krok 🎉',
            'desc': 'Zadej svou úplně první finanční transakci.',
            'unlocked': user_transactions.count() > 0
        },
        {
            'title': 'Velký střadatel 💰',
            'desc': 'Dosáhni celkových příjmů přesahujících 5 000 Kč.',
            'unlocked': total_income >= 5000
        },
        {
            'title': 'Finanční kontrola ⚖️',
            'desc': 'Udrž si kladnou aktuální bilanci (nejsi v mínusu).',
            'unlocked': current_balance > 0
        },
    ]

    # --- TRANSACTION CREATION PROCESSOR ---
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user  # Securely tie transaction to the logged-in user
            transaction.save()
            return redirect('dashboard')  # Reload dashboard to see fresh data
    else:
        form = TransactionForm()

    # Pass everything over to the HTML layer
    context = {
        'transactions': user_transactions,
        'total_income': total_income,
        'total_expense': total_expense,
        'current_balance': current_balance,
        'form': form,
        'achievements': achievements,
    }
    return render(request, 'dashboard.html', context)

@login_required
def add_transaction_ajax(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            
            # --- RE-CALCULATE AGGREGATES FOR AJAX RESPONSE ---
            user_transactions = Transaction.objects.filter(user=request.user)
            total_income = sum(tx.amount for tx in user_transactions if tx.transaction_type == 'INCOME')
            total_expense = sum(tx.amount for tx in user_transactions if tx.transaction_type == 'EXPENSE')
            current_balance = total_income - total_expense

            # Dynamic achievement check
            achievements = [
                {'title': 'První krok 🎉', 'unlocked': user_transactions.count() > 0},
                {'title': 'Velký střadatel 💰', 'unlocked': total_income >= 5000},
                {'title': 'Finanční kontrola ⚖️', 'unlocked': current_balance > 0},
            ]

            # Return success packet
            return JsonResponse({
                'status': 'success',
                'transaction': {
                    'date': transaction.date.strftime('%d. %m. %Y'),
                    'type': transaction.transaction_type,
                    'amount': str(transaction.amount),
                    'category': transaction.get_category_display(),
                    'description': transaction.description or '',
                },
                'metrics': {
                    'total_income': str(total_income),
                    'total_expense': str(total_expense),
                    'current_balance': str(current_balance),
                },
                'achievements': achievements
            })
        else:
            # Send back validation errors if user typed bad data
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)