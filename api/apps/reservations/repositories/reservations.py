from django.db.models import Count

from apps.reservations.models import Reservation
from common.repositories import BaseRepository


class ReservationRepository(BaseRepository[Reservation]):
    """Data access for reservations."""

    model = Reservation

    def get_by_cancel_token(self, token):
        return self.model.objects.filter(cancel_token=token).first()

    def get_oldest_substitute(self, batch):
        return self.model.objects.filter(batch=batch, is_substitute=True).order_by("created_at", "id").first()

    def list_for_batch_with_details(self, batch):
        return list(
            self.model.objects.select_related("faculty", "billing_information").filter(batch=batch).order_by("created_at", "id")
        )

    def count_in_batch(self, batch):
        return self.model.objects.filter(batch=batch).count()

    def count_substitutes_in_batch(self, batch):
        return self.model.objects.filter(batch=batch, is_substitute=True).count()

    def count_paid(self):
        return self.model.objects.filter(is_paid=True).count()

    def count_by_faculty(self):
        """Return a dict of faculty id to the number of its reservations."""
        rows = self.model.objects.values("faculty_id").annotate(total=Count("id"))
        counts = {}
        for row in rows:
            counts[row["faculty_id"]] = row["total"]
        return counts
