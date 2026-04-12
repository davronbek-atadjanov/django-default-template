from collections.abc import Sequence
from typing import Any

from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.utils.urls import replace_query_param


class CustomPagination(PageNumberPagination):  # type: ignore[misc]
    """
    PageNumber pagination with:
      - bounded page_size (max_page_size)
      - clear `meta` + `links` + `data` response shape
      - first / last links
      - OpenAPI schema via get_paginated_response_schema (drf-spectacular)
    """

    page_query_param = "page"
    page_size_query_param = "page_size"
    page_size = 20
    max_page_size = 100

    def get_page_size(self, request: Request | None) -> int:
        """
        Always return an int page size (never None). Enforce max_page_size.
        """
        raw = super().get_page_size(request)  # may return None or int
        if raw is None:
            return int(self.page_size)
        try:
            size = int(raw)
        except (TypeError, ValueError):
            return int(self.page_size)
        if self.max_page_size and size > int(self.max_page_size):
            return int(self.max_page_size)
        return size

    def _build_page_link(self, request: Request | None, page_number: int) -> str | None:
        """
        Build an absolute URI with the requested page number.
        If request is missing or building the URI fails, return None.
        """
        if not request:
            return None
        try:
            absolute = request.build_absolute_uri()
        except Exception:
            return None
        return replace_query_param(absolute, self.page_query_param, page_number)

    def get_paginated_response(self, data: Sequence[Any]) -> Response:
        """
        Standardized paginated response:
        {
          "success": True,
          "message": "Data fetched successfully.",
          "meta": { total_items, total_pages, page_size, current_page },
          "links": { first, last, next, previous },
          "data": [...]
        }
        """
        paginator = self.page.paginator
        page_size = int(self.get_page_size(self.request))
        total_pages = int(getattr(paginator, "num_pages", 0))
        current_page = int(getattr(self.page, "number", 1))

        first_link = self._build_page_link(self.request, 1) if total_pages > 0 else None
        last_link = self._build_page_link(self.request, total_pages) if total_pages > 0 else None

        return Response(
            {
                "success": True,
                "message": "Data fetched successfully.",
                "meta": {
                    "total_items": int(getattr(paginator, "count", 0)),
                    "total_pages": total_pages,
                    "page_size": page_size,
                    "current_page": current_page,
                },
                "links": {
                    "first": first_link,
                    "last": last_link,
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                },
                "data": data,
            }
        )

    # drf-spectacular: provide OpenAPI schema for paginated responses
    def get_paginated_response_schema(self, schema: dict[str, Any]) -> dict[str, Any]:
        """
        `schema` parameter is the OpenAPI schema for the page `data` items (e.g. serializer schema).
        Return a mapping representing the final response object schema.
        """
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean", "example": True},
                "message": {"type": "string", "example": "Data fetched successfully."},
                "meta": {
                    "type": "object",
                    "properties": {
                        "total_items": {"type": "integer", "example": 120},
                        "total_pages": {"type": "integer", "example": 6},
                        "page_size": {"type": "integer", "example": 20},
                        "current_page": {"type": "integer", "example": 1},
                    },
                    "required": ["total_items", "total_pages", "page_size", "current_page"],
                },
                "links": {
                    "type": "object",
                    "properties": {
                        "first": {"type": ["string", "null"], "example": "http://api.example.com/resource?page=1"},
                        "last": {"type": ["string", "null"], "example": "http://api.example.com/resource?page=6"},
                        "next": {"type": ["string", "null"], "example": "http://api.example.com/resource?page=2"},
                        "previous": {"type": ["string", "null"], "example": None},
                    },
                },
                "data": schema,
            },
            "required": ["success", "message", "meta", "links", "data"],
        }
