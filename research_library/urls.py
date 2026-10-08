from django.urls import path
from . import views

urlpatterns = [
    path('', views.paper_list_view, name='paper_list'),
    path('<int:paper_id>/', views.paper_detail_view, name='paper_detail'),
    path('upload/', views.upload_paper_view, name='upload_paper'),
]