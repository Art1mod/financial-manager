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
from budget.views import (
    dashboard, 
    register, 
    change_currency_ajax, 
    add_transaction_ajax, 
    delete_transaction_ajax,
    update_transaction_ajax,        
    get_transaction_details         
)
from achievements.views import get_achievements_ajax

urlpatterns = [
    path('admin/', admin.site.urls),
    
    #  Route the landing root path directly to dashboard layout page
    path('', RedirectView.as_view(url='dashboard/', permanent=False)),
    path('get-achievements/', get_achievements_ajax, name='get_achievements'),
    
    #  Authentication Routing Points
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', register, name='register'),
    
    #  Application Workspace Infrastructure
    path('dashboard/', dashboard, name='dashboard'),
    path('add-transaction-ajax/', add_transaction_ajax, name='add_transaction_ajax'),
    path('change-currency-ajax/', change_currency_ajax, name='change_currency_ajax'),

    path('delete-transaction/<int:transaction_id>/', delete_transaction_ajax, name='delete_transaction_ajax'),
    path('get-transaction/<int:transaction_id>/', get_transaction_details, name='get_transaction_details'),
    path('update-transaction/<int:transaction_id>/', update_transaction_ajax, name='update_transaction_ajax'),
]
