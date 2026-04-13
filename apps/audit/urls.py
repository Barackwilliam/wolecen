from django.urls import path
from . import views

app_name = 'audit'

urlpatterns = [
    path('log/', views.audit_log_view, name='log'),
    path('reports/', views.reports_view, name='reports'),
]
