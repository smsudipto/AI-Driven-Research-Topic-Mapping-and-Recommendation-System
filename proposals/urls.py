from django.urls import path
from . import views

urlpatterns = [
    path('topics/', views.topic_list_view, name='topic_list'),
    path('topics/create/', views.create_topic_view, name='create_topic'),
    path('topics/<int:topic_id>/edit/', views.edit_topic_view, name='edit_topic'),
    path('topics/<int:topic_id>/toggle-status/', views.toggle_topic_status_view, name='toggle_topic_status'),
    path('topics/<int:topic_id>/request/', views.request_proposal_view, name='request_proposal'),
    path('', views.proposal_list_view, name='proposal_list'),
    path('my-proposals/', views.my_proposals_view, name='my_proposals'),
    path('create/', views.create_proposal_view, name='create_proposal'),
    path('contact-student/<str:student_id>/', views.contact_student_view, name='contact_student'),
    path('contact-supervisor/<int:supervisor_id>/', views.contact_supervisor_view, name='contact_supervisor'),
    path('review/<int:proposal_id>/', views.review_proposal_view, name='review_proposal'),
    path('review-request/<int:request_id>/', views.review_request_view, name='review_request'),
]