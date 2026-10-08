from django.urls import path
from . import views

urlpatterns = [
    path('', views.group_dashboard_view, name='group_dashboard'),
    path('my-progress/', views.my_progress_view, name='my_progress'),
    path('student-progress/', views.student_progress_view, name='student_progress'),
    path('group/<int:group_id>/', views.group_detail_view, name='group_detail'),
    path('group/<int:group_id>/create-milestone/', views.create_milestone_view, name='create_milestone'),
    path('milestone/<int:milestone_id>/update/', views.update_milestone_status_view, name='update_milestone'),
    path('milestone/<int:milestone_id>/submit/', views.update_milestone_view, name='submit_milestone'),
]