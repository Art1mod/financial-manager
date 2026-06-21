from django import forms
from .models import Transaction

class TransactionForm(forms.ModelForm):
    category = forms.ChoiceField(choices=[('', '---------')])
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        limit = self.fields['description'].max_length
        self.fields['description'].widget.attrs.update({
            'rows': 3,
            'maxlength': limit,
            'data-max-length': limit, 
            'placeholder': f'Popis (max {limit} znaků)...'
        })
        self.fields['category'].choices = Transaction.CATEGORY_CHOICES
    
    class Meta:
        model = Transaction
        fields = ['transaction_type', 'category','amount', 'currency', 'description']
        widgets = {
            'description': forms.Textarea(),
        }