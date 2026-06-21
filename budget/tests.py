# budget/tests.py

from django.test import TestCase
from django.contrib.auth.models import User
from .models import Transaction
from .forms import TransactionForm

class BudgetAppTestCase(TestCase):

    def setUp(self):
        """Sets up a clean testing environment before each individual test runs."""
        
        self.user = User.objects.create_user(username='teststudent', password='password123')

    # --- TEST 1: FORM VALIDATION ---
    def test_transaction_form_valid_data(self):
        """Verifies that standard, well-formed form inputs pass validation rules successfully."""
        form_data = {
            'amount': '250.50',
            'transaction_type': 'INCOME',
            'category': 'OTHER',
            'description': 'Kapesné od babičky',
            'currency': 'CZK',
        }
        form = TransactionForm(data=form_data)
        self.assertTrue(form.is_valid(), "The form should be valid when all correct parameters are supplied.")

    def test_transaction_form_invalid_data(self):
        """Verifies that missing or malformed inputs fail validation safeguards gracefully."""
        form_data = {
            'amount': '', # Empty amount should fail!
            'transaction_type': 'UNKNOWN_TYPE', # Invalid choice should fail!
            'category': 'FOOD'
        }
        form = TransactionForm(data=form_data)
        self.assertFalse(form.is_valid(), "The form should catch structural flaws and reject validation.")

    # --- TEST 2: FINANCIAL MATH BALANCE CALCULATIONS ---
    def test_financial_math_calculations(self):
        """Verifies that income and expense aggregations yield correct mathematical balances."""
        
        Transaction.objects.create(user=self.user, amount=10000.00, transaction_type='INCOME', category='OTHER')
        Transaction.objects.create(user=self.user, amount=2000.00, transaction_type='EXPENSE', category='FOOD')

        user_txs = Transaction.objects.filter(user=self.user)
        total_income = sum(tx.amount for tx in user_txs if tx.transaction_type == 'INCOME')
        total_expense = sum(tx.amount for tx in user_txs if tx.transaction_type == 'EXPENSE')
        current_balance = total_income - total_expense

        self.assertEqual(total_income, 10000.00)
        self.assertEqual(total_expense, 2000.00)
        self.assertEqual(current_balance, 8000.00)
