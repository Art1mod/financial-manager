from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .models import Transaction
from .forms import TransactionForm

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
    }
    return render(request, 'dashboard.html', context)