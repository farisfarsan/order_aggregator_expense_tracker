from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('authorize/', views.authorize, name='authorize'),
    path('oauth2callback/', views.oauth2callback, name='oauth2callback'),
    path('summary/', views.summary, name='summary'),
    path('sync_gmail/', views.sync_gmail, name='sync_gmail'),
    path('sync/', views.sync_gmail, name='sync'),  # ✅ Add this line
    path('dashboard/', views.dashboard, name='dashboard'),
]
