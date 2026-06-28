from django.http import HttpResponse
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.viewsets import ViewSet

from apps.reservations.dtos import (
    CancelRequestSerializer,
    PublicOverviewResponseSerializer,
    ReservationCreateRequestSerializer,
    ReservationResponseSerializer,
)
from apps.reservations.services import reservation_service


class ReservationController(ViewSet):
    """Public API endpoints for the registration form and the cancel link from the email."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "public"

    def list(self, request):
        overview = reservation_service.get_public_overview()
        return Response(PublicOverviewResponseSerializer(overview).data)

    def create(self, request):
        serializer = ReservationCreateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        billing = data["billing_information"]
        reservation = reservation_service.create(
            name=data["name"],
            surname=data["surname"],
            email=data["email"],
            faculty_id=data["faculty_id"],
            year=data["year"],
            batch_number=data["batch"],
            nickname=data["nickname"],
            disability=data["disability"],
            roommate=data["roommate"],
            gdpr_consent=data["gdpr_consent"],
            newsletter_consent=data["newsletter_consent"],
            billing_city=billing["city"],
            billing_street=billing["street"],
            billing_postal_code=billing["postal_code"],
            billing_country=billing["country"],
            billing_phone=billing["phone"],
            image=data["image"],
        )
        return Response(ReservationResponseSerializer(reservation).data)

    @action(detail=False, methods=["get"], url_path=r"cancel/(?P<token>[0-9a-fA-F-]{36})")
    def cancel(self, request, token):
        serializer = CancelRequestSerializer(data={"token": token})
        serializer.is_valid(raise_exception=True)
        reservation_id = reservation_service.cancel_by_token(token=serializer.validated_data["token"])
        text = f"Rezervace {reservation_id} zrušena. Více informací v emailu."
        return HttpResponse(text, content_type="text/plain; charset=utf-8")
