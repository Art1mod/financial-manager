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

    # Links transaction to a specific user. If user is deleted, their transactions are deleted.
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=7, choices=TRANSACTION_TYPES)
    category = models.CharField(max_length=15, choices=CATEGORIES, default='OTHER')
    description = models.CharField(max_length=255, blank=True)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type}: {self.amount} Kč ({self.category})"
    
class Achievement(models.Model):
    # This acts as a master list of available awards
    title = models.CharField(max_length=100)
    description = models.TextField()
    badge_code = models.CharField(max_length=50, unique=True) # e.g., 'first_1000', '10_trans'

    def __str__(self):
        return self.title

class UserAchievement(models.Model):
    # Tracks which user has unlocked which achievement and when
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='unlocked_achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    date_unlocked = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'achievement') # Prevents unlocking the same achievement twice

    def __str__(self):
        return f"{self.user.username} unlocked {self.achievement.title}"