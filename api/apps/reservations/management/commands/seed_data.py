from django.core.management.base import BaseCommand

from apps.faculties.services import faculty_service
from apps.reservations.services import batch_service


class Command(BaseCommand):
    """Management command that loads the reference data."""

    help = "Load the reference data (faculties and camp batches). Safe to run repeatedly."

    def handle(self, *args, **options):
        faculty_count = faculty_service.seed_reference_data()
        batch_count = batch_service.seed_reference_data()
        self.stdout.write(self.style.SUCCESS(f"Created {faculty_count} faculties and {batch_count} batches."))
