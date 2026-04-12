from django.http import HttpRequest, JsonResponse
from django.views import View
from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = "index.html"


class HealthCheckView(View):
    """Lightweight health endpoint for Docker Swarm / load balancer checks."""

    def get(self, request: HttpRequest) -> JsonResponse:
        return JsonResponse({"status": "ok"})


def custom_handler404(
    request: HttpRequest,
    exception: Exception | None = None,
) -> JsonResponse:
    return JsonResponse(
        {
            "success": False,
            "message": "Not Found",
        },
        status=404,
    )


def custom_handler500(request: HttpRequest) -> JsonResponse:
    return JsonResponse(
        {
            "success": False,
            "message": "Server Error",
        },
        status=500,
    )


def custom_handler403(
    request: HttpRequest,
    exception: Exception | None = None,
) -> JsonResponse:
    return JsonResponse(
        {
            "success": False,
            "message": "Forbidden",
        },
        status=403,
    )


def custom_handler400(
    request: HttpRequest,
    exception: Exception | None = None,
) -> JsonResponse:
    return JsonResponse(
        {
            "success": False,
            "message": "Bad Request",
        },
        status=400,
    )
