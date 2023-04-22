"""calendar URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
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
from django.urls import path
from . import views
from django.shortcuts import redirect


urlpatterns = [
    path('v1/calendar/init/', views.GoogleCalendarInitView, name='google_permission'),
    path('v1/calendar/redirect/', views.GoogleCalendarRedirectView, name='google_redirect'),
    path('', lambda req: redirect('v1/calendar/init/', permanent=False),name='root')
]