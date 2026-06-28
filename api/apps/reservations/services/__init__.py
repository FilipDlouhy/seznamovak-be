from apps.faculties.repositories import faculty_repository
from apps.reservations.repositories import batch_repository, billing_information_repository, reservation_repository

from .batches import BatchService
from .emails import ReservationEmailService
from .newsletter import NewsletterService
from .payment_qr import PaymentQrService
from .pdf import ReservationPdfService
from .reservations import ReservationService
from .stats import ReservationStatsService

batch_service = BatchService(batch_repository=batch_repository, reservation_repository=reservation_repository)
payment_qr_service = PaymentQrService()
email_service = ReservationEmailService(payment_qr_service=payment_qr_service)
newsletter_service = NewsletterService()
reservation_service = ReservationService(
    reservation_repository=reservation_repository,
    batch_repository=batch_repository,
    billing_information_repository=billing_information_repository,
    faculty_repository=faculty_repository,
    batch_service=batch_service,
    email_service=email_service,
    newsletter_service=newsletter_service,
)
reservation_stats_service = ReservationStatsService(
    reservation_repository=reservation_repository,
    faculty_repository=faculty_repository,
    batch_service=batch_service,
)
reservation_pdf_service = ReservationPdfService(
    reservation_repository=reservation_repository,
    batch_repository=batch_repository,
)

__all__ = [
    "batch_service",
    "reservation_pdf_service",
    "reservation_service",
    "reservation_stats_service",
]
