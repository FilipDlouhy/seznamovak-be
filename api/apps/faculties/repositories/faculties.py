from django.core.management.color import no_style
from django.db import connection

from apps.faculties.models import Faculty
from common.repositories import BaseRepository


class FacultyRepository(BaseRepository[Faculty]):
    """Data access for faculties."""

    model = Faculty

    def create_if_missing(self, *, faculty_id, faculty_name, faculty_abbrev):
        """Insert the faculty with a fixed id unless it exists, return True when it was created."""
        _, created = self.model.objects.get_or_create(
            id=faculty_id,
            defaults={"faculty_name": faculty_name, "faculty_abbrev": faculty_abbrev},
        )
        return created

    def reset_id_sequence(self):
        """Move the id sequence past the fixed ids so new faculties do not collide with them."""
        statements = connection.ops.sequence_reset_sql(no_style(), [self.model])
        with connection.cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)
