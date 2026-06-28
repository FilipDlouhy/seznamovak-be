import logging
from functools import partial

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

SUBJECT_CONFIRMATION = "Seznamovák UTB {year} - Potvrzení rezervace"
SUBJECT_SUBSTITUTE = "Seznamovák UTB {year} - Rezervace náhradníka"
SUBJECT_CANCELLED = "Seznamovák UTB {year} - Zrušení rezervace"
SUBJECT_PAYMENT = "Seznamovák UTB {year} - Platba přijata"

TEXT_CONFIRMATION = "Tvoje registrace na Seznamovák UTB {year} byla přijata. Podrobnosti najdeš v HTML verzi tohoto e-mailu."
TEXT_SUBSTITUTE = "Jsi na seznamu náhradníků na Seznamovák UTB {year}. Pokud se uvolní místo, ozveme se Ti."
TEXT_CANCELLED = "Tvoje rezervace na Seznamovák UTB {year} byla zrušena."
TEXT_PAYMENT = "Tvou platbu zálohy na Seznamovák UTB {year} jsme obdrželi a registrace je potvrzena."


class ReservationEmailService:
    """Builds the reservation emails and sends them after the surrounding transaction commits."""

    def __init__(self, *, payment_qr_service):
        self.payment_qr_service = payment_qr_service

    def send_confirmation(self, *, reservation):
        """Confirmation with payment instructions and both QR codes."""
        self._queue(
            reservation=reservation,
            subject=SUBJECT_CONFIRMATION,
            text=TEXT_CONFIRMATION,
            template="reservations/emails/reservation.html",
            with_qr_codes=True,
        )

    def send_substitute_notice(self, *, reservation):
        self._queue(
            reservation=reservation,
            subject=SUBJECT_SUBSTITUTE,
            text=TEXT_SUBSTITUTE,
            template="reservations/emails/reservation_substitute.html",
            with_qr_codes=False,
        )

    def send_cancelled(self, *, reservation):
        self._queue(
            reservation=reservation,
            subject=SUBJECT_CANCELLED,
            text=TEXT_CANCELLED,
            template="reservations/emails/cancel.html",
            with_qr_codes=False,
        )

    def send_payment_received(self, *, reservation):
        self._queue(
            reservation=reservation,
            subject=SUBJECT_PAYMENT,
            text=TEXT_PAYMENT,
            template="reservations/emails/payment_received.html",
            with_qr_codes=False,
        )

    def _queue(self, *, reservation, subject, text, template, with_qr_codes):
        # The message is built now, while the reservation still exists, and sent only after the commit
        try:
            message = self._build(
                reservation=reservation,
                subject=subject,
                text=text,
                template=template,
                with_qr_codes=with_qr_codes,
            )
        except Exception:
            logger.exception("Could not build email '%s' for reservation %s", subject, reservation.pk)
            return
        transaction.on_commit(partial(self._deliver, message))

    def _build(self, *, reservation, subject, text, template, with_qr_codes):
        context = {
            "year": settings.SEZNAMOVAK_YEAR,
            "edition": settings.SEZNAMOVAK_EDITION,
            "deposit_czk": settings.SEZNAMOVAK_DEPOSIT_CZK,
            "deposit_eur": settings.SEZNAMOVAK_DEPOSIT_EUR,
            "balance_czk": settings.SEZNAMOVAK_BALANCE_CZK,
            "payment_deadline_days": settings.SEZNAMOVAK_PAYMENT_DEADLINE_DAYS,
            "account_czk": settings.SEZNAMOVAK_ACCOUNT_CZK,
            "account_eur": settings.SEZNAMOVAK_ACCOUNT_EUR,
            "iban_eur": settings.SEZNAMOVAK_IBAN_EUR,
            "variable_symbol": settings.SEZNAMOVAK_VARIABLE_SYMBOL,
            "turnus_number": reservation.batch.number,
            "turnus_date": reservation.batch.start_date.strftime("%d.%m.%Y"),
            "cancel_url": f"{settings.SEZNAMOVAK_PUBLIC_URL}/api/reservations/cancel/{reservation.cancel_token}",
        }
        html = render_to_string(template, context)
        message = EmailMultiAlternatives(
            subject=subject.format(year=settings.SEZNAMOVAK_YEAR),
            body=text.format(year=settings.SEZNAMOVAK_YEAR),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[reservation.email],
        )
        message.attach_alternative(html, "text/html")
        if with_qr_codes:
            for qr_image in self.payment_qr_service.build_images():
                message.attach(qr_image.file_name, qr_image.content, "image/png")
        return message

    def _deliver(self, message):
        try:
            message.send()
        except Exception:
            logger.exception("Could not send email '%s' to %s", message.subject, message.to)
