from django.conf import settings
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.user.urls")),
    re_path(r"^media/(?P<path>.*)$", staff_member_required(serve), {"document_root": settings.MEDIA_ROOT}),
]
