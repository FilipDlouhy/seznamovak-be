import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.faculties.models import Faculty


class Batch(models.Model):
    """Camp batch (turnus) with its capacity and dates."""

    number = models.PositiveIntegerField("Číslo turnusu", unique=True)
    capacity = models.PositiveIntegerField("Kapacita", default=100)
    start_date = models.DateField("Začátek")
    end_date = models.DateField("Konec")
    registration_opens_at = models.DateTimeField("Registrace začíná", null=True, blank=True)
    registration_closes_at = models.DateTimeField("Registrace končí", null=True, blank=True)

    class Meta:
        ordering = ["number"]
        verbose_name = "Turnus"
        verbose_name_plural = "Turnusy"

    def __str__(self):
        return f"{self.number}. turnus"


class BillingInformation(models.Model):
    """Address and phone of a registered student."""

    city = models.CharField("Město", max_length=255, blank=True, default="")
    street = models.CharField("Ulice", max_length=255, blank=True, default="")
    postal_code = models.CharField("PSČ", max_length=255, blank=True, default="")
    country = models.CharField("Země", max_length=255, blank=True, default="")
    phone = models.CharField("Telefon", max_length=255, blank=True, default="")

    class Meta:
        verbose_name = "Fakturační údaje"
        verbose_name_plural = "Fakturační údaje"

    def __str__(self):
        return f"{self.street}, {self.city}"


class Reservation(models.Model):
    """Student's registration for a camp batch, either a regular place or a substitute."""

    name = models.CharField("Jméno", max_length=255)
    surname = models.CharField("Příjmení", max_length=255)
    name_normalized = models.CharField("Jméno (bez diakritiky)", max_length=255, blank=True, default="")
    surname_normalized = models.CharField("Příjmení (bez diakritiky)", max_length=255, blank=True, default="")
    email = models.EmailField("E-mail", max_length=255)
    faculty = models.ForeignKey(Faculty, verbose_name="Fakulta", on_delete=models.PROTECT)
    year = models.PositiveSmallIntegerField(
        "Ročník",
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    nickname = models.CharField("Přezdívka", max_length=255, blank=True, default="")
    disability = models.CharField("Omezení", max_length=255, blank=True, default="")
    roommate = models.CharField("Spolubydlící", max_length=255, blank=True, default="")
    billing_information = models.OneToOneField(
        BillingInformation,
        verbose_name="Fakturační údaje",
        on_delete=models.PROTECT,
    )
    batch = models.ForeignKey(Batch, verbose_name="Turnus", on_delete=models.PROTECT)
    gdpr_consent = models.BooleanField("Souhlas s GDPR", default=False)
    newsletter_consent = models.BooleanField("Souhlas s newsletterem", default=False)
    is_paid = models.BooleanField("Zaplaceno", default=False)
    is_substitute = models.BooleanField("Náhradník", default=False)
    photo = models.ImageField("Fotka", upload_to="people", blank=True)
    cancel_token = models.UUIDField("Token pro zrušení", default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField("Vytvořeno", auto_now_add=True)
    updated_at = models.DateTimeField("Upraveno", auto_now=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Rezervace"
        verbose_name_plural = "Rezervace"

    def __str__(self):
        return f"{self.name} {self.surname} (#{self.pk})"
