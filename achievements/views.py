# achievements/views.py

from django.template.loader import render_to_string
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.template import Template, Context

from .models import UserAchievement

@login_required
def get_achievements_ajax(request):
    """Returns updated rendered HTML snippets for the frontend to swap in."""
    
    # 1. Get recent unlocked badges
    recent_achievements = UserAchievement.objects.filter(
        user=request.user
    ).order_by('-date_unlocked')[:3]
        
    recent_html = render_to_string(
        'achievements/recent_achievements_widget.html',
        {'recent_achievements': recent_achievements}
    )
        
    # 2. Render the full achievement grid via template tags
    template = Template("{% load gamification_tags %}{% render_user_achievements user %}")
    all_html = template.render(Context({'user': request.user}))
        
    return JsonResponse({
        'status': 'success',
        'recent_html': recent_html,
         'all_html': all_html
    })
