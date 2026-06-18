from apps.faculties.repositories import faculty_repository

from .faculties import FacultyService

faculty_service = FacultyService(faculty_repository=faculty_repository)

__all__ = ["faculty_service"]
