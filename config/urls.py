from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('complaints/', include('complaints.urls')),
    path('pickups/', include('pickups.urls')),
    path('manage/', include('complaints.admin_urls')),
    path('collector/', include('complaints.collector_urls')),
    path('tasks/', include('complaints.task_urls')),
    path('awareness/', include('awareness.urls')),
    path('feedback/', include('feedback.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)