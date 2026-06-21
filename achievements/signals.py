# achievements/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from budget.models import Transaction
from .models import Achievement, UserAchievement

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from budget.models import Transaction
from .models import Achievement, UserAchievement

from budget.views import calculate_user_metrics

@receiver(post_save, sender=Transaction)
def evaluate_achievements_on_transaction(sender, instance, created, **kwargs):
    if not created:
        return 

    user = instance.user
    user_transactions = Transaction.objects.filter(user=user)
    
    # Helper function to unlock badges safely
    def unlock(code_str):
        try:
            ach = Achievement.objects.get(badge_code=code_str)
            UserAchievement.objects.get_or_create(user=user, achievement=ach)
        except Achievement.DoesNotExist:
            pass

    # --- CALCULATE METRICS ---
    metrics = calculate_user_metrics(user, 'CZK')
    current_balance = metrics['current_balance']
    
    total_count = user_transactions.count()
    today = timezone.localdate()
    transactions_today = user_transactions.filter(date__date=today).count()

    active_days = list(user_transactions.dates('date', 'day', order='DESC'))

    # ==========================================
    # 1. BALANCE MILESTONES
    # ==========================================
    if current_balance > 1000:
        unlock('first_1000')
    if current_balance >= 10000:
        unlock('first_10000')  
    if current_balance >= 100000:
        unlock('first_100000') 

    # ==========================================
    # 2. VOLUME MILESTONES
    # ==========================================
    if total_count >= 10:
        unlock('10_trans')
    if total_count >= 50:
        unlock('50_trans') 
    if total_count >= 100:
        unlock('100_trans') 

    # ==========================================
    # 3. FIRSTS (TYPE SPECIFIC)
    # ==========================================
    if instance.transaction_type == 'INCOME':
        unlock('first_income') 
    if instance.transaction_type == 'EXPENSE':
        unlock('first_expense')
    if transactions_today == 1:
        unlock('first_of_day')

    # ==========================================
    # 4. CONSISTENCY STREAKS
    # ==========================================
    
    # 3-Day Logging Streak 
    if len(active_days) >= 3:
        if (active_days[0] - active_days[2]).days == 2:
            unlock('3_day_streak')

    # 5-Day Logging Streak 
    if len(active_days) >= 5:
        if (active_days[0] - active_days[4]).days == 4:
            unlock('5_day_streak')

    # ==========================================
    # 5. NO-EXPENSE STREAKS
    # ==========================================
    
    expenses = user_transactions.filter(transaction_type='EXPENSE').order_by('-date')
    
    if expenses.exists():
        last_expense_date = expenses.first().date.date()
        days_since_expense = (today - last_expense_date).days
        
        if days_since_expense >= 3:
            unlock('no_expense_3_days') 
        if days_since_expense >= 7:
            unlock('no_expense_7_days') 
    else:
        if len(active_days) > 0:
            days_active = (today - active_days[-1]).days
            if days_active >= 3:
                unlock('no_expense_3_days')
            if days_active >= 7:
                unlock('no_expense_7_days')