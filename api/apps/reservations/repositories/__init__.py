from .batches import BatchRepository
from .billing_information import BillingInformationRepository
from .reservations import ReservationRepository

batch_repository = BatchRepository()
billing_information_repository = BillingInformationRepository()
reservation_repository = ReservationRepository()

__all__ = ["batch_repository", "billing_information_repository", "reservation_repository"]
