from django.contrib import admin
from .models import Transaction, Achievement, UserAchievement

admin.site.register(Transaction)
admin.site.register(Achievement)
admin.site.register(UserAchievement)# Register your models here.
