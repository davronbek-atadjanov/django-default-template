from __future__ import annotations

from typing import Any

from django.contrib.auth.decorators import login_required
from django.urls import path
from django.utils.translation import gettext_lazy as _
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


def _make_prefix_filter(prefix: str):  # type: ignore[no-untyped-def]
    def preprocessing_hook(endpoints: list[Any]) -> list[Any]:
        return [ep for ep in endpoints if ep[0].startswith(prefix)]

    return preprocessing_hook


class ClientSchemaView(SpectacularAPIView):
    custom_settings: dict[str, Any] = {
        "TITLE": _("Cargo Client API"),
        "DESCRIPTION": _("Client (mobil ilova) uchun API"),
        "PREPROCESSING_HOOKS": ["core.config.swagger._client_filter"],
    }

    def _get_schema_generator(self) -> SchemaGenerator:
        generator = super()._get_schema_generator()
        generator.inspector.spectacular_settings.update(self.custom_settings)  # type: ignore[union-attr]
        return generator


class AdminSchemaView(SpectacularAPIView):
    custom_settings: dict[str, Any] = {
        "TITLE": _("Cargo Admin API"),
        "DESCRIPTION": _("Admin panel uchun API"),
        "PREPROCESSING_HOOKS": ["core.config.swagger._admin_filter"],
    }

    def _get_schema_generator(self) -> SchemaGenerator:
        generator = super()._get_schema_generator()
        generator.inspector.spectacular_settings.update(self.custom_settings)  # type: ignore[union-attr]
        return generator


class WMSSchemaView(SpectacularAPIView):
    custom_settings: dict[str, Any] = {
        "TITLE": _("Cargo WMS API"),
        "DESCRIPTION": _("WMS panel uchun API"),
        "PREPROCESSING_HOOKS": ["core.config.swagger._wms_filter"],
    }

    def _get_schema_generator(self) -> SchemaGenerator:
        generator = super()._get_schema_generator()
        generator.inspector.spectacular_settings.update(self.custom_settings)  # type: ignore[union-attr]
        return generator


def _client_filter(endpoints: list[Any]) -> list[Any]:
    return [ep for ep in endpoints if ep[0].startswith("/api/v1/client/")]


def _admin_filter(endpoints: list[Any]) -> list[Any]:
    return [ep for ep in endpoints if ep[0].startswith("/api/v1/admin/")]


def _wms_filter(endpoints: list[Any]) -> list[Any]:
    return [ep for ep in endpoints if ep[0].startswith("/api/v1/wms/")]


urlpatterns = [
    # Client API docs
    path(
        "api/v1/client/schema/",
        ClientSchemaView.as_view(),
        name="client-schema",
    ),
    path(
        "api/v1/client/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="client-schema"),
        name="client-swagger-ui",
    ),
    path(
        "api/v1/client/schema/redoc/",
        SpectacularRedocView.as_view(url_name="client-schema"),
        name="client-redoc",
    ),
    # Admin API docs (login required)
    path(
        "api/v1/admin/schema/",
        login_required(AdminSchemaView.as_view(), login_url="/admin/"),
        name="admin-schema",
    ),
    path(
        "api/v1/admin/schema/swagger-ui/",
        login_required(SpectacularSwaggerView.as_view(url_name="admin-schema"), login_url="/admin/"),
        name="admin-swagger-ui",
    ),
    path(
        "api/v1/admin/schema/redoc/",
        login_required(SpectacularRedocView.as_view(url_name="admin-schema"), login_url="/admin/"),
        name="admin-redoc",
    ),
]
