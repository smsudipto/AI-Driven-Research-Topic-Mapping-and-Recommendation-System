from django.urls import path
from . import views

app_name = 'core_ai'

urlpatterns = [
    path('search/', views.search_novelty_view, name='search'),
    path('match/<int:proposal_id>/', views.match_proposal_view, name='match_proposal'),
    path('api/match-score/<int:proposal_id>/', views.match_score_api, name='match_score_api'),
]