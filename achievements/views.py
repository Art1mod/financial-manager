from django.shortcuts import render

from django.template.loader import render_to_string
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Achievement, UserAchievement

@login_required
def get_achievements_ajax(request):
    """Returns updated rendered HTML snippets for the frontend to swap in."""
    # Data for the "All Achievements" grid
    all_achievements = Achievement.objects.all()
    unlocked_badges = UserAchievement.objects.filter(user=request.user).values_list('achievement__badge_code', flat=True)
    
    context_all = []
    for ach in all_achievements:
        context_all.append({
            'title': ach.title, 'desc': ach.description, 'unlocked': ach.badge_code in unlocked_badges
        })
    
    # Data for the "Recent" banner
    recent_badges = UserAchievement.objects.filter(user=request.user).select_related('achievement').order_by('-date_unlocked')[:2]
    
    # Render the snippets directly to HTML strings
    all_html = render_to_string('achievements/achievements_widget.html', {'achievements': context_all})
    recent_html = render_to_string('achievements/recent_achievements_widget.html', {'recent_achievements': recent_badges})

    return JsonResponse({'all_html': all_html, 'recent_html': recent_html})
