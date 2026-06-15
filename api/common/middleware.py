from django.utils import translation


class ApiEnglishMiddleware:
    """Answers /api/ requests in English while the admin stays Czech."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith("/api/"):
            return self.get_response(request)
        with translation.override("en"):
            return self.get_response(request)
