from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Transaction, Achievement, UserAchievement

@receiver(post_save, sender=Transaction)
def check_achievements_on_save(sender, instance, created, **kwargs):
    if not created:
        return # Only calculate milestones when a fresh transaction is added

    user = instance.user
    user_transactions = Transaction.objects.filter(user=user)

    # --- CALCULATE METRICS ---
    total_income = sum(tx.amount for tx in user_transactions if tx.transaction_type == 'INCOME')
    total_expense = sum(tx.amount for tx in user_transactions if tx.transaction_type == 'EXPENSE')
    current_balance = total_income - total_expense
    total_count = user_transactions.count()

    # Get today's range in user local time context
    today = timezone.localdate()
    transactions_today = user_transactions.filter(date=today).count()

    # Helper function to safely unlock an achievement row
    def unlock(code_str):
        try:
            ach = Achievement.objects.get(badge_code=code_str)
            UserAchievement.objects.get_or_create(user=user, achievement=ach)
        except Achievement.DoesNotExist:
            pass # Skips if you haven't typed the dummy achievement into the admin panel yet

    # --- MILESTONE 1: Has user saved > 1000 Kč total? ---
    if current_balance > 1000:
        unlock('first_1000')

    # --- MILESTONE 2: Does user have >= 10 transaction records? ---
    if total_count >= 10:
        unlock('10_trans')

    # --- MILESTONE 3: Is this the first transaction of the day? ---
    if transactions_today == 1:
        unlock('first_of_day')