# achievements/templatetags/gamification_tags.py
from django import template
from achievements.models import Achievement, UserAchievement

register = template.Library()

@register.inclusion_tag('achievements/achievements_widget.html')
def render_user_achievements(user):
    """Fetches user achievements and renders them via a dedicated HTML snippet."""
    all_achievements = Achievement.objects.all()
    unlocked_badges = UserAchievement.objects.filter(user=user).values_list('achievement__badge_code', flat=True)
    
    achievements_context = []
    for ach in all_achievements:
        achievements_context.append({
            'title': ach.title,
            'desc': ach.description,
            'unlocked': ach.badge_code in unlocked_badges
        })
        
    return {'achievements': achievements_context}

@register.inclusion_tag('achievements/recent_achievements_widget.html')
def render_recent_achievements(user):
    """Fetches only unlocked achievements for the top banner."""
    unlocked_badges = UserAchievement.objects.filter(user=user).select_related('achievement').order_by('-date_unlocked')[:2]
    return {'recent_achievements': unlocked_badges}