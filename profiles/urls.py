from django.urls import path
from . import views

urlpatterns = [
    # View user profile (Automatically routes based on user role: Student/Supervisor)
    path('', views.profile_view, name='profile'),
    
    # Edit user profile form
    path('edit/', views.edit_profile_view, name='edit_profile'),
    
    # Find supervisors page with search and filter functionality
    path('find-supervisor/', views.find_supervisor, name='profiles_find_supervisor'),

    # Supervisor detail page for students and visitors
    path('supervisors/<int:supervisor_id>/', views.supervisor_detail_view, name='supervisor_detail'),

    # Student contact preparation page for supervisors
    path('contact-supervisor/<int:supervisor_id>/', views.contact_supervisor_view, name='profiles_contact_supervisor'),

    # Supervisor-only student search page
    path('find-students/', views.find_students, name='profiles_find_students'),

    # Student detail page for supervisor browsing
    path('students/<str:student_id>/', views.student_detail_view, name='student_detail'),
]