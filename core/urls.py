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
from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

# Group your imports by app to keep them tidy
from budget import views as budget_views
from achievements import views as achievement_views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Landing
    path('', RedirectView.as_view(url='dashboard/', permanent=False)),
    
    # Auth
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', budget_views.register, name='register'),
    
    # Budget Workspace
    path('dashboard/', budget_views.dashboard, name='dashboard'),
    path('add-transaction-ajax/', budget_views.add_transaction_ajax, name='add_transaction_ajax'),
    path('change-currency-ajax/', budget_views.change_currency_ajax, name='change_currency_ajax'),
    path('delete-transaction/<int:transaction_id>/', budget_views.delete_transaction_ajax, name='delete_transaction_ajax'),
    path('get-transaction/<int:transaction_id>/', budget_views.get_transaction_details, name='get_transaction_details'),
    path('update-transaction/<int:transaction_id>/', budget_views.update_transaction_ajax, name='update_transaction_ajax'),
    
    # Achievements
    path('get-achievements/', achievement_views.get_achievements_ajax, name='get_achievements'),
]
