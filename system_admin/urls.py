from django.urls import path
from . import views

urlpatterns = [
    path('logs/', views.system_logs_view, name='system_logs'),
    path('logs/<int:log_id>/', views.log_detail_view, name='log_detail'),
    path('logs/clear/', views.clear_logs_view, name='clear_logs'),
]