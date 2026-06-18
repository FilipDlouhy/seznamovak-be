from django.db import transaction

# The ids are fixed because the public form posts them
FACULTIES = [
    (1, "Fakulta technologická", "FT"),
    (2, "Fakulta managementu a ekonomiky", "FAME"),
    (3, "Fakulta multimediálních komunikací", "FMK"),
    (4, "Fakulta aplikované informatiky", "FAI"),
    (5, "Fakulta humanitních studií", "FHS"),
    (6, "Fakulta logistiky a krizového řízení", "FLKŘ"),
]


class FacultyService:
    """Faculty reference data."""

    def __init__(self, *, faculty_repository):
        self.faculty_repository = faculty_repository

    @transaction.atomic
    def seed_reference_data(self):
        """Create the missing faculties, return how many were created."""
        created_count = 0
        for faculty_id, faculty_name, faculty_abbrev in FACULTIES:
            created = self.faculty_repository.create_if_missing(
                faculty_id=faculty_id,
                faculty_name=faculty_name,
                faculty_abbrev=faculty_abbrev,
            )
            if created:
                created_count += 1
        self.faculty_repository.reset_id_sequence()
        return created_count
