from django import forms
from .models import Transaction

class TransactionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        limit = self.fields['description'].max_length
        self.fields['description'].widget.attrs.update({
            'rows': 3,
            'maxlength': limit,
            'data-max-length': limit, 
            'placeholder': f'Popis (max {limit} znaků)...'
        })
    
    class Meta:
        model = Transaction
        fields = ['transaction_type', 'amount', 'category', 'description', 'currency']
        widgets = {
            'description': forms.Textarea(),
        }