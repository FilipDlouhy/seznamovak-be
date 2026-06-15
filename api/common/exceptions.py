from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler


def build_validation_body(errors):
    """Laravel validation body: a message plus the errors by field."""
    return {"message": "The given data was invalid.", "errors": errors}


class ApplicationError(Exception):
    """Base exception for application errors, converted to an HTTP response."""

    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, message, *, code=None):
        super().__init__(message)
        self.message = message
        self.code = code

    def to_data(self):
        data = {"detail": self.message}
        if self.code:
            data["code"] = self.code
        return data


class ValidationFailedError(ApplicationError):
    """Input validation failed; the field errors are returned as they are."""

    def __init__(self, errors):
        super().__init__("Invalid input.")
        self.errors = errors

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

    def to_data(self):
        return build_validation_body(self.errors)


class NotFoundError(ApplicationError):
    """Resource not found."""

    status_code = status.HTTP_404_NOT_FOUND


class ConflictError(ApplicationError):
    """The operation is not allowed in the current state."""

    status_code = status.HTTP_409_CONFLICT


class AuthenticationError(ApplicationError):
    """Request lacks valid credentials."""

    status_code = status.HTTP_401_UNAUTHORIZED


def custom_exception_handler(exc, context):
    """Convert ApplicationError and Django ValidationError to REST responses."""
    if isinstance(exc, ApplicationError):
        response = Response(exc.to_data(), status=exc.status_code)
        if isinstance(exc, AuthenticationError):
            response["WWW-Authenticate"] = 'Bearer realm="api"'
        return response
    if isinstance(exc, DRFValidationError):
        # Laravel answers invalid input with 422
        return Response(build_validation_body(exc.detail), status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, "error_dict"):
            data = exc.message_dict
        else:
            data = {"detail": exc.messages}
        return Response(data, status=status.HTTP_400_BAD_REQUEST)
    return exception_handler(exc, context)
