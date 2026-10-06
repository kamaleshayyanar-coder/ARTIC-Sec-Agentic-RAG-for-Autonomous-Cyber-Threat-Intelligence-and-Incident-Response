"""Domain exceptions mapped to HTTP status codes."""


class ArticSecError(Exception):
    status_code = 500
    code = "internal_error"

    def __init__(self, message: str, *, detail: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail or message


class NotFoundError(ArticSecError):
    status_code = 404
    code = "not_found"


class UnauthorizedError(ArticSecError):
    status_code = 401
    code = "unauthorized"


class ForbiddenError(ArticSecError):
    status_code = 403
    code = "forbidden"


class ValidationAppError(ArticSecError):
    status_code = 422
    code = "validation_error"


class GuardrailRejectedError(ArticSecError):
    status_code = 409
    code = "guardrail_rejected"
