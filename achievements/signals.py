#achievements/signals.py

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

    # --- CALCULATE METRICS (The Fix) ---
    # 2. Ask the budget app for the true converted balance in CZK
    metrics = calculate_user_metrics(user, 'CZK')
    current_balance = metrics['current_balance']
    
    # Keep the basic counters for the other milestones
    total_count = user_transactions.count()
    today = timezone.localdate()
    transactions_today = user_transactions.filter(date__date=today).count()

    # --- MILESTONE 1: Has user saved > 1000 Kč total? ---
    if current_balance > 1000:
        unlock('first_1000')

    # --- MILESTONE 2: Does user have >= 10 transaction records? ---
    if total_count >= 10:
        unlock('10_trans')

    # --- MILESTONE 3: Is this the first transaction of the day? ---
    if transactions_today == 1:
        unlock('first_of_day')