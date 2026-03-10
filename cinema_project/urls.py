"""URL configuration for cinema_project project."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


admin.site.site_header = '🎬 Jegymester Adminisztráció'
admin.site.site_title = 'Jegymester Admin'
admin.site.index_title = 'Kezelőpanel'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('core.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
