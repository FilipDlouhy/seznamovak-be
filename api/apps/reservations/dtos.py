from dataclasses import dataclass
from datetime import date, datetime

from django.conf import settings
from rest_framework import serializers

from apps.faculties.dtos import FacultyResponseSerializer

BILLING_FIELDS = ["city", "street", "postal_code", "country", "phone"]


@dataclass(frozen=True)
class BatchOverview:
    """A batch with its free places and substitutes."""

    number: int
    start_date: date
    end_date: date
    capacity: int
    remaining: int
    substitutes: int
    registration_opens_at: datetime | None
    registration_closes_at: datetime | None


@dataclass(frozen=True)
class PriceOverview:
    """Camp prices from the settings."""

    total_czk: int
    total_eur: int
    deposit_czk: int
    deposit_eur: int
    balance_czk: int


@dataclass(frozen=True)
class PublicOverview:
    """Everything the public registration form needs."""

    faculties: list
    first_batch_capacity: int
    second_batch_capacity: int
    batches: list
    price: PriceOverview


@dataclass(frozen=True)
class FacultyStats:
    """Number of reservations of one faculty."""

    abbrev: str
    name: str
    total: int


@dataclass(frozen=True)
class ReservationStats:
    """Numbers shown above the reservation list in the admin."""

    total: int
    paid: int
    unpaid: int
    batches: list
    faculties: list


class BillingInformationRequestSerializer(serializers.Serializer):
    """Billing address sent as the multipart keys billing_information[city] and so on."""

    city = serializers.CharField(max_length=255)
    street = serializers.CharField(max_length=255)
    postal_code = serializers.CharField(max_length=255)
    country = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=255)

    def get_value(self, dictionary):
        values = {}
        for field_name in BILLING_FIELDS:
            key = f"billing_information[{field_name}]"
            if key in dictionary:
                values[field_name] = dictionary[key]
        return values


class ReservationCreateRequestSerializer(serializers.Serializer):
    """Body of POST /api/reservations."""

    name = serializers.CharField(max_length=255)
    surname = serializers.CharField(max_length=255)
    email = serializers.EmailField(max_length=255)
    faculty_id = serializers.IntegerField()
    year = serializers.IntegerField(min_value=1, max_value=5)
    batch = serializers.IntegerField()
    nickname = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    disability = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    roommate = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    gdpr_consent = serializers.BooleanField()
    newsletter_consent = serializers.BooleanField(required=False, default=False)
    image = serializers.ImageField()
    billing_information = BillingInformationRequestSerializer()

    def validate_gdpr_consent(self, value):
        if not value:
            raise serializers.ValidationError("GDPR consent is required.")
        return value

    def validate_image(self, value):
        if value.size > settings.PHOTO_MAX_BYTES:
            raise serializers.ValidationError("The photo is too large.")
        if value.image.format not in settings.PHOTO_ALLOWED_FORMATS:
            raise serializers.ValidationError("The photo must be a JPEG or PNG image.")
        return value


class CancelRequestSerializer(serializers.Serializer):
    """Token from the cancel link."""

    token = serializers.UUIDField()


class ReservationResponseSerializer(serializers.Serializer):
    """The created reservation."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    surname = serializers.CharField()
    email = serializers.EmailField()
    faculty_id = serializers.IntegerField()
    year = serializers.IntegerField()
    nickname = serializers.CharField()
    disability = serializers.CharField()
    roommate = serializers.CharField()
    billing_information_id = serializers.IntegerField()
    gdpr_consent = serializers.BooleanField()
    newsletter_consent = serializers.BooleanField()
    is_paid = serializers.BooleanField()
    batch = serializers.IntegerField(source="batch.number")
    is_substitute = serializers.BooleanField()
    name_normalized = serializers.CharField()
    surname_normalized = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class BatchOverviewResponseSerializer(serializers.Serializer):
    """One batch in the public overview."""

    number = serializers.IntegerField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    capacity = serializers.IntegerField()
    remaining = serializers.IntegerField()
    substitutes = serializers.IntegerField()
    registration_opens_at = serializers.DateTimeField(allow_null=True)
    registration_closes_at = serializers.DateTimeField(allow_null=True)


class PriceOverviewResponseSerializer(serializers.Serializer):
    """Prices in the public overview."""

    total_czk = serializers.IntegerField()
    total_eur = serializers.IntegerField()
    deposit_czk = serializers.IntegerField()
    deposit_eur = serializers.IntegerField()
    balance_czk = serializers.IntegerField()


class PublicOverviewResponseSerializer(serializers.Serializer):
    """Response of GET /api/reservations."""

    faculties = FacultyResponseSerializer(many=True)
    firstBatchCapacity = serializers.IntegerField(source="first_batch_capacity")
    secondBatchCapacity = serializers.IntegerField(source="second_batch_capacity")
    batches = BatchOverviewResponseSerializer(many=True)
    price = PriceOverviewResponseSerializer()
