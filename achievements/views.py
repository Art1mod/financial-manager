# achievements/views.py

from django.template.loader import render_to_string
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Achievement, UserAchievement
from django.template import Template, Context

@login_required
def get_achievements_ajax(request):
    """Returns updated rendered HTML snippets for the frontend to swap in."""
    recent_achievements = UserAchievement.objects.filter(
        user=request.user
    ).order_by('-date_unlocked')[:3]
        
    recent_html = render_to_string(
        'achievements/recent_achievements_widget.html',
        {'recent_achievements': recent_achievements}
    )
        
    template = Template("{% load gamification_tags %}{% render_user_achievements user %}")
    all_html = template.render(Context({'user': request.user}))
        
    return JsonResponse({
        'status': 'success',
        'recent_html': recent_html,
         'all_html': all_html
    })
