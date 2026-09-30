from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("store.urls")),
]

# Product images (MEDIA_URL / MEDIA_ROOT) are served by Django in development only.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "store.views.handler404"
