from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import dashboard_view
from profiles.views import find_supervisor, find_students
from proposals.views import proposal_list_view, topic_list_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard_view, name='dashboard'),  # Root URL points to Dashboard
    path('accounts/', include('accounts.urls')),
    path('profiles/', include('profiles.urls')),
    path('find-supervisor/', find_supervisor, name='find_supervisor'),
    path('find-students/', find_students, name='find_students'),
    path('topics/', topic_list_view, name='topics'),
    path('proposals/', include('proposals.urls')),
    path('received-proposals/', proposal_list_view, name='received_proposals'),
    path('library/', include('research_library.urls')),
    path('progress/', include('progress_tracker.urls')),
    path('ai/', include('core_ai.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# from django.contrib import admin
# from django.urls import path, include

# urlpatterns = [
#     path('admin/', admin.site.urls),
    
#     # Active App
#     path('accounts/', include('accounts.urls')),
    
#     # Temporarily commented out until views are ready
#     # path('profile/', include('profiles.urls')),
#     # path('proposals/', include('proposals.urls')),
#     # path('library/', include('research_library.urls')),
#     # path('progress/', include('progress_tracker.urls')),
#     # path('ai/', include('core_ai.urls')),
#     # path('system/', include('system_admin.urls')),
# ]
