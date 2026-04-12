from django.conf import settings
from django.urls import path

from apps.shared.api.v1.views.base import HealthCheckView, HomeView

urlpatterns = [
    path("api/health/", HealthCheckView.as_view(), name="health"),
]

if settings.DEBUG:
    urlpatterns += [
        path("", HomeView.as_view(), name="home"),
    ]
