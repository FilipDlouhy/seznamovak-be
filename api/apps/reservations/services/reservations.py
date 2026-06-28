import unicodedata

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.reservations.dtos import PriceOverview, PublicOverview
from apps.reservations.models import BillingInformation, Reservation
from common.exceptions import ConflictError, NotFoundError, ValidationFailedError

FIRST_BATCH_NUMBER = 1
SECOND_BATCH_NUMBER = 2

# The 2026 form sends it for an empty optional text field
EMPTY_PLACEHOLDER = "---"


def remove_accents(text):
    """Strip diacritics, so a surname like Čech becomes Cech."""
    decomposed = unicodedata.normalize("NFKD", text)
    result = ""
    for char in decomposed:
        if not unicodedata.combining(char):
            result += char
    return result


def clean_optional_text(text):
    """Turn the form placeholder for an empty field into an empty string."""
    if text.strip() == EMPTY_PLACEHOLDER:
        return ""
    return text


class ReservationService:
    """Registration, cancellation and payment of camp reservations."""

    def __init__(
        self,
        *,
        reservation_repository,
        batch_repository,
        billing_information_repository,
        faculty_repository,
        batch_service,
        email_service,
        newsletter_service,
    ):
        self.reservation_repository = reservation_repository
        self.batch_repository = batch_repository
        self.billing_information_repository = billing_information_repository
        self.faculty_repository = faculty_repository
        self.batch_service = batch_service
        self.email_service = email_service
        self.newsletter_service = newsletter_service

    def get_public_overview(self):
        """Faculties, the batches with their free places, and the prices for the public form."""
        first_batch = self._get_batch_or_raise(FIRST_BATCH_NUMBER)
        second_batch = self._get_batch_or_raise(SECOND_BATCH_NUMBER)
        price = PriceOverview(
            total_czk=settings.SEZNAMOVAK_PRICE_TOTAL_CZK,
            total_eur=settings.SEZNAMOVAK_PRICE_TOTAL_EUR,
            deposit_czk=settings.SEZNAMOVAK_DEPOSIT_CZK,
            deposit_eur=settings.SEZNAMOVAK_DEPOSIT_EUR,
            balance_czk=settings.SEZNAMOVAK_BALANCE_CZK,
        )
        return PublicOverview(
            faculties=self.faculty_repository.get_all(),
            first_batch_capacity=self.batch_service.remaining_capacity(batch=first_batch),
            second_batch_capacity=self.batch_service.remaining_capacity(batch=second_batch),
            batches=self.batch_service.get_overviews(),
            price=price,
        )

    @transaction.atomic
    def create(
        self,
        *,
        name,
        surname,
        email,
        faculty_id,
        year,
        batch_number,
        nickname,
        disability,
        roommate,
        gdpr_consent,
        newsletter_consent,
        billing_city,
        billing_street,
        billing_postal_code,
        billing_country,
        billing_phone,
        image,
    ):
        faculty = self.faculty_repository.get_by_id(faculty_id)
        if faculty is None:
            raise ValidationFailedError({"faculty_id": ["Faculty does not exist."]})

        # The batch row is locked so two requests cannot take the last place at the same time
        batch = self.batch_repository.get_by_number_for_update(batch_number)
        if batch is None:
            raise ValidationFailedError({"batch": ["Batch does not exist."]})

        self._check_registration_window(batch)

        is_substitute = self.batch_service.remaining_capacity(batch=batch) == 0

        billing_information = BillingInformation(
            city=billing_city,
            street=billing_street,
            postal_code=billing_postal_code,
            country=billing_country,
            phone=billing_phone,
        )
        self.billing_information_repository.save(billing_information)

        reservation = Reservation(
            name=name,
            surname=surname,
            name_normalized=remove_accents(name),
            surname_normalized=remove_accents(surname),
            email=email,
            faculty=faculty,
            year=year,
            nickname=clean_optional_text(nickname),
            disability=clean_optional_text(disability),
            roommate=clean_optional_text(roommate),
            billing_information=billing_information,
            batch=batch,
            gdpr_consent=gdpr_consent,
            newsletter_consent=newsletter_consent,
            is_substitute=is_substitute,
        )
        self.reservation_repository.save(reservation)

        # The file name contains the id, so the photo can only be saved after the reservation
        photo_name = f"{reservation.name_normalized}{reservation.surname_normalized}{reservation.pk}.jpg"
        reservation.photo.save(photo_name, image, save=False)
        self.reservation_repository.save(reservation, update_fields=["photo"], validate=False)

        if is_substitute:
            self.email_service.send_substitute_notice(reservation=reservation)
        else:
            self.email_service.send_confirmation(reservation=reservation)
        if newsletter_consent:
            self.newsletter_service.subscribe(email=reservation.email)
        return reservation

    @transaction.atomic
    def cancel_by_token(self, *, token):
        """Cancel the reservation with this token and return its id."""
        reservation = self.reservation_repository.get_by_cancel_token(token)
        if reservation is None:
            raise NotFoundError("Reservation not found.")
        return self.cancel(reservation_id=reservation.pk)

    @transaction.atomic
    def cancel(self, *, reservation_id):
        """Delete the reservation, send the cancel email and move the oldest substitute up."""
        reservation = self.reservation_repository.get_by_id(reservation_id)
        if reservation is None:
            raise NotFoundError("Reservation not found.")

        # Lock the batch first, then reload the reservation, so a double click cancels only once
        batch = self.batch_repository.get_by_id_for_update(reservation.batch_id)
        reservation = self.reservation_repository.get_by_id_for_update(reservation_id)
        if reservation is None:
            raise NotFoundError("Reservation not found.")

        billing_information = reservation.billing_information
        self.email_service.send_cancelled(reservation=reservation)
        # A cancelled substitute frees no place, so only a regular reservation promotes the next substitute
        if not reservation.is_substitute:
            self._promote_oldest_substitute(batch)

        reservation.photo.delete(save=False)
        self.reservation_repository.delete(reservation)
        self.billing_information_repository.delete(billing_information)
        return reservation_id

    @transaction.atomic
    def mark_paid(self, *, reservation_id):
        """Set the reservation paid and send the payment confirmation."""
        reservation = self.reservation_repository.get_by_id_for_update(reservation_id)
        if reservation is None:
            raise NotFoundError("Reservation not found.")
        if reservation.is_substitute:
            raise ConflictError("A substitute cannot be marked as paid.")
        if reservation.is_paid:
            raise ConflictError("The reservation is already paid.")
        reservation.is_paid = True
        self.reservation_repository.save(reservation, update_fields=["is_paid", "updated_at"], validate=False)
        self.email_service.send_payment_received(reservation=reservation)
        return reservation

    def _get_batch_or_raise(self, number):
        batch = self.batch_repository.get_by_number(number)
        if batch is None:
            raise NotFoundError(f"Batch {number} does not exist.")
        return batch

    def _check_registration_window(self, batch):
        """Refuse the registration before the batch opens and after it closes; an empty bound means no limit."""
        now = timezone.now()
        if batch.registration_opens_at is not None and now < batch.registration_opens_at:
            raise ConflictError("Registration has not started yet.")
        if batch.registration_closes_at is not None and now >= batch.registration_closes_at:
            raise ConflictError("Registration is closed.")

    def _promote_oldest_substitute(self, batch):
        substitute = self.reservation_repository.get_oldest_substitute(batch)
        if substitute is None:
            return
        substitute.is_substitute = False
        self.reservation_repository.save(substitute, update_fields=["is_substitute", "updated_at"], validate=False)
        self.email_service.send_confirmation(reservation=substitute)
