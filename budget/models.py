# budget/models.py

from django.db import models
from django.contrib.auth.models import User

class Transaction(models.Model):
    
    #Transaction Types
    INCOME_CATEGORIES = [
        ('SALARY', 'Plat'),
        ('DIVIDEND', 'Dividendy'),
        ('BONUS', 'Bonus'),
        ('OTHER_INC', 'Ostatní Příjem'),
    ]
    EXPENSE_CATEGORIES = [
        ('FOOD', 'Jídlo'),
        ('RENT', 'Bydlení'),
        ('TRANSPORT', 'Doprava'),
        ('FUN', 'Zábava'),
        ('OTHER_EXP', 'Ostatní Výdaj'),
    ]
    

    CURRENCY_CHOICES = [
        ('CZK', 'Kč (CZK)'),
        ('USD', '$ (USD)'),
        ('EUR', '€ (EUR)'),
    ]

    CATEGORY_CHOICES = INCOME_CATEGORIES + EXPENSE_CATEGORIES

    # Links transaction to a specific user. If user is deleted, their transactions are deleted.
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=[('INCOME', 'Příjem'), ('EXPENSE', 'Výdaj')])
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.CharField(max_length=255, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='CZK')

    def __str__(self):
        currency_symbols = {
            'CZK': 'Kč',
            'USD': '$',
            'EUR': '€'
        }
        symbol = currency_symbols.get(self.currency, self.currency)
        type_label = self.get_transaction_type_display()
        category_label = self.get_category_display()
        
        return f"{self.user.username} - {type_label}: {self.amount} {symbol} ({category_label})"
    