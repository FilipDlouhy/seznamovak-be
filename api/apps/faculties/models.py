from django.db import models


class Faculty(models.Model):
    """Faculty of the university a student can register from."""

    faculty_name = models.CharField("Název fakulty", max_length=255)
    faculty_abbrev = models.CharField("Zkratka fakulty", max_length=255)
    created_at = models.DateTimeField("Vytvořeno", auto_now_add=True)
    updated_at = models.DateTimeField("Upraveno", auto_now=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "Fakulta"
        verbose_name_plural = "Fakulty"

    def __str__(self):
        return self.faculty_abbrev
