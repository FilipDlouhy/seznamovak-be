from django.contrib import admin

from .models import Faculty


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    """Admin for faculties."""

    list_display = ["id", "faculty_abbrev", "faculty_name"]
    search_fields = ["faculty_name", "faculty_abbrev"]
