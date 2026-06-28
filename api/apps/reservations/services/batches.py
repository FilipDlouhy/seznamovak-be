from datetime import date, datetime
from zoneinfo import ZoneInfo

from django.db import transaction

from apps.reservations.dtos import BatchOverview

PRAGUE = ZoneInfo("Europe/Prague")

REGISTRATION_OPENS_AT = datetime(2026, 7, 20, 15, 0, tzinfo=PRAGUE)
REGISTRATION_CLOSES_AT = datetime(2026, 8, 24, 15, 0, tzinfo=PRAGUE)

# number, capacity, start date, end date, registration opens at, registration closes at
BATCHES = [
    (1, 100, date(2026, 8, 17), date(2026, 8, 20), REGISTRATION_OPENS_AT, REGISTRATION_CLOSES_AT),
    (2, 100, date(2026, 8, 24), date(2026, 8, 27), REGISTRATION_OPENS_AT, REGISTRATION_CLOSES_AT),
]


class BatchService:
    """Batch capacity, overview and reference data."""

    def __init__(self, *, batch_repository, reservation_repository):
        self.batch_repository = batch_repository
        self.reservation_repository = reservation_repository

    def remaining_capacity(self, *, batch):
        """Free places of the batch; substitutes occupy places too, so it never goes below zero."""
        reserved = self.reservation_repository.count_in_batch(batch)
        return max(batch.capacity - reserved, 0)

    def get_overviews(self):
        overviews = []
        for batch in self.batch_repository.get_all():
            overviews.append(
                BatchOverview(
                    number=batch.number,
                    start_date=batch.start_date,
                    end_date=batch.end_date,
                    capacity=batch.capacity,
                    remaining=self.remaining_capacity(batch=batch),
                    substitutes=self.reservation_repository.count_substitutes_in_batch(batch),
                    registration_opens_at=batch.registration_opens_at,
                    registration_closes_at=batch.registration_closes_at,
                )
            )
        return overviews

    @transaction.atomic
    def seed_reference_data(self):
        """Create the missing batches, return how many were created."""
        created_count = 0
        for number, capacity, start_date, end_date, opens_at, closes_at in BATCHES:
            created = self.batch_repository.create_if_missing(
                number=number,
                capacity=capacity,
                start_date=start_date,
                end_date=end_date,
                registration_opens_at=opens_at,
                registration_closes_at=closes_at,
            )
            if created:
                created_count += 1
        return created_count
