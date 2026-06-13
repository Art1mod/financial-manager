"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from budget.views import register

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Built-in Django login/logout routes (looks inside templates/registration/)
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Custom registration route
    path('accounts/register/', register, name='register'),
    
    # A temporary landing page so the app doesn't crash before the dashboard is being built
    path('', TemplateView.as_view(template_name='dashboard_temp.html'), name='dashboard'),
]
