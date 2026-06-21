# achievements/tests.py

from django.test import TestCase
from django.contrib.auth.models import User
from budget.models import Transaction
from .models import Achievement, UserAchievement
from django.utils import timezone
from datetime import timedelta

class BudgetAppTestCase(TestCase):

    def setUp(self):
        """Sets up a clean testing environment and creates all required achievements."""
        self.user = User.objects.create_user(username='testuser', password='password123')

        # 1. Balance Milestones
        self.ach_1000 = Achievement.objects.create(badge_code='first_1000', title='První krok', description='Naspoř 1 000 Kč.')
        self.ach_10000 = Achievement.objects.create(badge_code='first_10000', title='Střadatel', description='Naspoř 10 000 Kč.')
        self.ach_100000 = Achievement.objects.create(badge_code='first_100000', title='Magnát', description='Naspoř 100 000 Kč.')

        # 2. Volume Milestones
        self.ach_10 = Achievement.objects.create(badge_code='10_trans', title='Veterán', description='10 transakcí.')
        self.ach_50 = Achievement.objects.create(badge_code='50_trans', title='Zkušený', description='50 transakcí.')
        self.ach_100 = Achievement.objects.create(badge_code='100_trans', title='Mistr', description='100 transakcí.')
        self.ach_day = Achievement.objects.create(badge_code='first_of_day', title='Ranní ptáče', description='První dnes.')

        # 3. Consistency Streaks
        self.ach_3_streak = Achievement.objects.create(badge_code='3_day_streak', title='Na vlně', description='3 dny v řadě.')
        self.ach_5_streak = Achievement.objects.create(badge_code='5_day_streak', title='Disciplína', description='5 dní v řadě.')

        # 4. No-Expense Streaks
        self.ach_no_exp_3 = Achievement.objects.create(badge_code='no_expense_3_days', title='Šetřílek', description='3 dny bez výdajů.')
        self.ach_no_exp_7 = Achievement.objects.create(badge_code='no_expense_7_days', title='Asketik', description='7 dní bez výdajů.')

    def create_historical_transaction(self, days_ago, amount, t_type='INCOME'):
        """
        Helper method to create a transaction in the past. 
        Uses .update() to bypass auto_now_add and avoid triggering signals prematurely.
        """
        tx = Transaction.objects.create(user=self.user, amount=amount, transaction_type=t_type, category='OTHER')
        target_date = timezone.now() - timedelta(days=days_ago)
        Transaction.objects.filter(id=tx.id).update(date=target_date)
        return tx

    def has_achievement(self, achievement_obj):
        """Helper method to check if the user has a specific achievement."""
        return UserAchievement.objects.filter(user=self.user, achievement=achievement_obj).exists()
    
    # ==========================================
    # TEST 1: BALANCE MILESTONES
    # ==========================================
    def test_balance_milestones(self):
        # Add 1,500
        Transaction.objects.create(user=self.user, amount=1500, transaction_type='INCOME', category='OTHER')
        self.assertTrue(self.has_achievement(self.ach_1000))
        self.assertFalse(self.has_achievement(self.ach_10000))

        # Add 9,000 (Total 10,500)
        Transaction.objects.create(user=self.user, amount=9000, transaction_type='INCOME', category='OTHER')
        self.assertTrue(self.has_achievement(self.ach_10000))
        self.assertFalse(self.has_achievement(self.ach_100000))

        # Add 90,000 (Total 100,500)
        Transaction.objects.create(user=self.user, amount=90000, transaction_type='INCOME', category='OTHER')
        self.assertTrue(self.has_achievement(self.ach_100000))

    # ==========================================
    # TEST 2: VOLUME MILESTONES
    # ==========================================
    def test_volume_milestones(self):
        # Create 9 transactions
        for _ in range(9):
            Transaction.objects.create(user=self.user, amount=10, transaction_type='INCOME', category='OTHER')
        
        self.assertFalse(self.has_achievement(self.ach_10))

        # 10th transaction
        Transaction.objects.create(user=self.user, amount=10, transaction_type='INCOME', category='OTHER')
        self.assertTrue(self.has_achievement(self.ach_10))
        self.assertFalse(self.has_achievement(self.ach_50))

        # Add 40 more (Total 50)
        for _ in range(40):
            Transaction.objects.create(user=self.user, amount=10, transaction_type='INCOME', category='OTHER')
        self.assertTrue(self.has_achievement(self.ach_50))
        self.assertFalse(self.has_achievement(self.ach_100))

        # Check 'first_of_day' was awarded during these creations
        self.assertTrue(self.has_achievement(self.ach_day))

    # ==========================================
    # TEST 3: CONSISTENCY STREAKS
    # ==========================================
    def test_consistency_streaks(self):
        # Create transactions for 4 days ago, 3 days ago, 2 days ago, 1 day ago
        self.create_historical_transaction(4, 100)
        self.create_historical_transaction(3, 100)
        self.create_historical_transaction(2, 100)
        self.create_historical_transaction(1, 100)

        # Confirm no streak badges are awarded yet (because signals weren't triggered for today)
        self.assertFalse(self.has_achievement(self.ach_3_streak))
        self.assertFalse(self.has_achievement(self.ach_5_streak))

        # Trigger the evaluation by creating a transaction TODAY
        Transaction.objects.create(user=self.user, amount=100, transaction_type='INCOME', category='OTHER')

        # User now has 5 days in a row (today, -1, -2, -3, -4)
        self.assertTrue(self.has_achievement(self.ach_3_streak))
        self.assertTrue(self.has_achievement(self.ach_5_streak))

    # ==========================================
    # TEST 4: NO-EXPENSE STREAKS
    # ==========================================
    def test_no_expense_streaks_with_prior_expense(self):
        # User made an expense 8 days ago
        self.create_historical_transaction(8, 500, t_type='EXPENSE')

        # Add an income today. This should trigger the check.
        # Since 8 days have passed since the last expense, both badges should unlock.
        Transaction.objects.create(user=self.user, amount=100, transaction_type='INCOME', category='OTHER')
        
        self.assertTrue(self.has_achievement(self.ach_no_exp_3))
        self.assertTrue(self.has_achievement(self.ach_no_exp_7))

    def test_no_expense_streak_reset(self):
        # User made an expense 2 days ago
        self.create_historical_transaction(2, 500, t_type='EXPENSE')

        # Add an income today. 
        Transaction.objects.create(user=self.user, amount=100, transaction_type='INCOME', category='OTHER')
        
        # Only 2 days have passed, so no badges should unlock
        self.assertFalse(self.has_achievement(self.ach_no_exp_3))
        self.assertFalse(self.has_achievement(self.ach_no_exp_7))