from django.db import models
from django.contrib.auth.models import User

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('INCOME', 'Příjem'),
        ('EXPENSE', 'Výdaj'),
    ]
    
    CATEGORIES = [
        ('FOOD', 'Jídlo'),
        ('RENT', 'Bydlení/Nájem'),
        ('TRANSPORT', 'Doprava'),
        ('ENTERTAINMENT', 'Zábava'),
        ('OTHER', 'Ostatní'),
    ]

    CURRENCY_CHOICES = [
        ('CZK', 'Kč (CZK)'),
        ('USD', '$ (USD)'),
        ('EUR', '€ (EUR)'),
    ]

    # Links transaction to a specific user. If user is deleted, their transactions are deleted.
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=7, choices=TRANSACTION_TYPES)
    category = models.CharField(max_length=15, choices=CATEGORIES, default='OTHER')
    description = models.CharField(max_length=255, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='CZK')

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type}: {self.amount} Kč ({self.category})"
    