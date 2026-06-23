from apps.reservations.models import BillingInformation
from common.repositories import BaseRepository


class BillingInformationRepository(BaseRepository[BillingInformation]):
    """Data access for billing information."""

    model = BillingInformation
