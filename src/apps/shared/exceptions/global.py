from typing import Any

from rest_framework.exceptions import (
    AuthenticationFailed,
    MethodNotAllowed,
    NotAcceptable,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    Throttled,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler

from apps.shared.utils.logger import logger

try:
    from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

    HAS_SIMPLEJWT = True
except ImportError:
    HAS_SIMPLEJWT = False

    class TokenError(Exception):  # type: ignore[no-redef]
        pass

    class InvalidToken(TokenError):  # type: ignore[no-redef]
        pass


def flatten_validation_errors(
    detail: Any,
    parent_field: str | None = None,
) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []

    if isinstance(detail, dict):
        for field, value in detail.items():
            full_field = f"{parent_field}.{field}" if parent_field else field
            errors.extend(flatten_validation_errors(value, full_field))

    elif isinstance(detail, list):
        for item in detail:
            errors.extend(flatten_validation_errors(item, parent_field))

    else:
        errors.append(
            {
                "field": parent_field or "non_field_error",
                "message": str(detail),
            }
        )

    return errors


def _extract_field_and_message(detail: Any) -> tuple[str | None, str]:
    """
    Returns (field_name_or_None, message_str) extracted from various DRF ValidationError shapes:
    - dict: {"field": ["err"]} -> ("field", "err")
    - dict nested: {"parent": {"child": ["err"]}} -> ("parent.child", "err")
    - list of dicts: [{"field": ["err"]}] -> ("field", "err")
    - simple list or single error -> (None, "error text")
    """
    # dict case: pick the first field
    if isinstance(detail, dict):
        first_key = next(iter(detail))
        value = detail[first_key]

        # nested dict like {"parent": {"child": ["err"]}}
        if isinstance(value, dict):
            nested_key = next(iter(value))
            nested_val = value[nested_key]
            # nested_val could be list/ErrorDetail/string
            if isinstance(nested_val, (list, tuple)) and nested_val:
                msg = str(nested_val[0])
            else:
                msg = str(nested_val)
            field = f"{first_key}.{nested_key}"
            return field, msg

        # typical case: value is list or ErrorDetail
        if isinstance(value, (list, tuple)) and value:
            # value[0] can be a dict (rare), list, or ErrorDetail
            first_item = value[0]
            if isinstance(first_item, dict):
                # { "field": [{"subfield": ["err"]}] } -> try to extract
                sub_key = next(iter(first_item))
                sub_val = first_item[sub_key]
                if isinstance(sub_val, (list, tuple)) and sub_val:
                    return f"{first_key}.{sub_key}", str(sub_val[0])
                return f"{first_key}.{sub_key}", str(sub_val)
            return first_key, str(first_item)
        # fallback
        return first_key, str(value)

    # list case: pick first element
    if isinstance(detail, (list, tuple)) and detail:
        first = detail[0]
        if isinstance(first, dict):
            fk = next(iter(first))
            fv = first[fk]
            if isinstance(fv, (list, tuple)) and fv:
                return fk, str(fv[0])
            return fk, str(fv)
        return None, str(first)

    # other (string/ErrorDetail)
    return None, str(detail)


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """
    Custom exception handler for standard API response format.

    Handles all DRF exceptions and unhandled server errors (500).

    Args:
        exc: The exception instance
        context: Additional context (view, request, etc.)

    Returns:
        Response with standard error format or None
    """

    response = exception_handler(exc, context)

    # Handle SimpleJWT token errors
    if HAS_SIMPLEJWT and isinstance(exc, (InvalidToken, TokenError)):
        # Extract human-readable message from the nested detail structure
        detail = getattr(exc, "detail", {})
        if isinstance(detail, dict):
            # Try to get 'messages' list first (most informative)
            messages = detail.get("messages", [])
            if messages and isinstance(messages, list):
                first_msg = messages[0]
                token_message = str(first_msg.get("message", "")) if isinstance(first_msg, dict) else str(first_msg)
            else:
                token_message = str(detail.get("detail", "Token is invalid or expired"))
        else:
            token_message = str(detail) if detail else "Token is invalid or expired"

        status_code = getattr(response, "status_code", 401) if response is not None else 401
        return Response(
            {
                "success": False,
                "message": token_message,
                "data": [
                    {
                        "field": "non_field_error",
                        "message": token_message,
                    }
                ],
            },
            status=status_code,
        )

    if isinstance(exc, ValidationError):
        if response is None:
            return None
        errors = flatten_validation_errors(exc.detail)
        field, message = _extract_field_and_message(exc.detail)
        if field and field != "non_field_error":
            full_message = f"{message}"
        else:
            full_message = message
        response.data = {
            "success": False,
            "message": full_message,
            "data": errors,
        }
        return response

    default_messages = {
        AuthenticationFailed: "Incorrect authentication credentials.",
        NotAuthenticated: "Authentication credentials were not provided.",
        PermissionDenied: "You do not have permission to perform this action.",
        NotFound: "Not found.",
        MethodNotAllowed: "Method not allowed.",
        Throttled: "Request was throttled.",
        NotAcceptable: "Not acceptable.",
    }

    if response is not None:
        for exc_cls, default_message in default_messages.items():
            if isinstance(exc, exc_cls):
                message = str(getattr(exc, "detail", "")).strip()
                response.data = {
                    "success": False,
                    "message": message or default_message,
                    "data": [
                        {
                            "field": "non_field_error",
                            "message": message or default_message,
                        }
                    ],
                }
                return response

        # Handle other DRF exceptions with response
        message = str(getattr(exc, "detail", str(exc))).strip()
        response.data = {
            "success": False,
            "message": message,
        }
        return response

    # Unhandled exceptions (500 Internal Server Error)
    logger.exception(f"Unhandled exception: {exc}", exc_info=True)
    return Response(
        {
            "success": False,
            "message": "Internal server error",
        },
        status=500,
    )
