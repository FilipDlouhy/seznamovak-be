from apps.reservations.models import Batch
from common.repositories import BaseRepository


class BatchRepository(BaseRepository[Batch]):
    """Data access for camp batches."""

    model = Batch

    def get_by_number(self, number):
        return self.model.objects.filter(number=number).first()

    def get_by_number_for_update(self, number):
        return self.model.objects.select_for_update().filter(number=number).first()

    def create_if_missing(self, *, number, capacity, start_date, end_date, registration_opens_at, registration_closes_at):
        """Insert the batch unless its number exists, return True when it was created."""
        _, created = self.model.objects.get_or_create(
            number=number,
            defaults={
                "capacity": capacity,
                "start_date": start_date,
                "end_date": end_date,
                "registration_opens_at": registration_opens_at,
                "registration_closes_at": registration_closes_at,
            },
        )
        return created
