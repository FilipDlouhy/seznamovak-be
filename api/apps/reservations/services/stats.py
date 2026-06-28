from apps.reservations.dtos import FacultyStats, ReservationStats


class ReservationStatsService:
    """Numbers for the reservation list in the admin."""

    def __init__(self, *, reservation_repository, faculty_repository, batch_service):
        self.reservation_repository = reservation_repository
        self.faculty_repository = faculty_repository
        self.batch_service = batch_service

    def get_stats(self):
        total = self.reservation_repository.count()
        paid = self.reservation_repository.count_paid()
        return ReservationStats(
            total=total,
            paid=paid,
            unpaid=total - paid,
            batches=self.batch_service.get_overviews(),
            faculties=self._faculty_stats(),
        )

    def _faculty_stats(self):
        counts = self.reservation_repository.count_by_faculty()
        result = []
        for faculty in self.faculty_repository.get_all():
            result.append(
                FacultyStats(
                    abbrev=faculty.faculty_abbrev,
                    name=faculty.faculty_name,
                    total=counts.get(faculty.pk, 0),
                )
            )
        return result
