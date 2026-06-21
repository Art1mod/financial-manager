# achievements/models.py

from django.db import models
from django.contrib.auth.models import User

class Achievement(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    badge_code = models.CharField(max_length=50, unique=True) # e.g., 'first_1000', '10_trans'

    def __str__(self):
        return self.title

# Tracks which user has unlocked which achievement and when
class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='unlocked_achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    date_unlocked = models.DateTimeField(auto_now_add=True)

    # Prevents unlocking the same achievement twice
    class Meta:
        unique_together = ('user', 'achievement') 

    def __str__(self):
        return f"{self.user.username} unlocked {self.achievement.title}"
