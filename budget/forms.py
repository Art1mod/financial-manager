from django import forms
from .models import Transaction

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        # Fields the user fills out manually. We exclude 'user' and 'created_at' 
        # because the backend handles those automatically!
        fields = ['transaction_type', 'amount', 'category', 'description', 'currency']