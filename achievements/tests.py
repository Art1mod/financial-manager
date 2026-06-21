from django.test import TestCase
from django.contrib.auth.models import User
from budget.models import Transaction
from .models import Achievement, UserAchievement

class BudgetAppTestCase(TestCase):

    def setUp(self):
        """Sets up a clean testing environment before each individual test runs."""
        
        self.user = User.objects.create_user(username='teststudent', password='password123')

        self.ach_1000 = Achievement.objects.create(
            badge_code='first_1000',
            title='První krok 🎉',
            description='Naspoř si více než 1 000 Kč.'
        )
        self.ach_10 = Achievement.objects.create(
            badge_code='10_trans',
            title='Finanční veterán 💰',
            description='Dosáhni milníku zaznamenáním alespoň 10 transakcí.'
        )
        self.ach_day = Achievement.objects.create(
            badge_code='first_of_day',
            title='Ranní ptáče ⚖️',
            description='První transakce dnes.'
        )

    def test_gamification_logic_triggers_and_locks(self):
        """Verifies that background signals smoothly log achievements accurately without duplication."""
        
        # Test Milestone 3: First transaction of the day should trigger instantly on your first record
        tx1 = Transaction.objects.create(user=self.user, amount=100.00, transaction_type='INCOME', category='OTHER')
        
        has_day_badge = UserAchievement.objects.filter(user=self.user, achievement=self.ach_day).exists()
        self.assertTrue(has_day_badge, "Milestone 3 should fire automatically on the first transaction of the day.")

        # Test Milestone 1: Has user saved > 1000 Kč total? 
        has_balance_badge = UserAchievement.objects.filter(user=self.user, achievement=self.ach_1000).exists()
        self.assertFalse(has_balance_badge, "User shouldn't unlock balance achievement while balance is under 1000 Kč.")

        #add 1500 Kč -> total balance 1600 Kč
        Transaction.objects.create(user=self.user, amount=1500.00, transaction_type='INCOME', category='OTHER')
        has_balance_badge_now = UserAchievement.objects.filter(user=self.user, achievement=self.ach_1000).exists()
        self.assertTrue(has_balance_badge_now, "Milestone 1 should unlock automatically once balance clears 1000 Kč.")

        # Test Safeguard: Ensure multiple saving transactions DO NOT create duplicate UserAchievement entries
        Transaction.objects.create(user=self.user, amount=500.00, transaction_type='INCOME', category='OTHER')
        balance_badge_count = UserAchievement.objects.filter(user=self.user, achievement=self.ach_1000).count()
        self.assertEqual(balance_badge_count, 1, "An achievement record must never log duplicate entries for the same user.")
