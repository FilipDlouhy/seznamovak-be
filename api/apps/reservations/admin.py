from django.contrib import admin, messages
from django.http import Http404, HttpResponse
from django.urls import path
from django.utils.html import format_html

from apps.reservations.models import Batch, Reservation
from apps.reservations.services import reservation_pdf_service, reservation_service, reservation_stats_service
from common.exceptions import ApplicationError, NotFoundError


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    """Admin for batches, including the registration window."""

    list_display = ["number", "capacity", "start_date", "end_date", "registration_opens_at", "registration_closes_at"]


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    """Admin for reservations with the summary, the actions and the PDF export."""

    list_display = [
        "photo_link",
        "full_name",
        "nickname",
        "email",
        "phone",
        "faculty_abbrev",
        "batch_number",
        "created_at",
        "roommate",
        "state",
    ]
    list_select_related = ["faculty", "batch", "billing_information"]
    list_filter = ["batch", "is_paid", "is_substitute", "faculty"]
    search_fields = ["name", "surname", "name_normalized", "surname_normalized", "email", "billing_information__phone"]
    ordering = ["created_at"]
    fields = [
        "name",
        "surname",
        "name_normalized",
        "surname_normalized",
        "email",
        "faculty",
        "year",
        "nickname",
        "disability",
        "roommate",
        "batch",
        "billing_address",
        "gdpr_consent",
        "newsletter_consent",
        "is_paid",
        "is_substitute",
        "photo_link",
        "cancel_token",
        "created_at",
        "updated_at",
    ]
    readonly_fields = ["billing_address", "photo_link", "cancel_token", "created_at", "updated_at"]
    actions = ["mark_paid", "cancel_reservations"]
    change_list_template = "admin/reservations/reservation/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        pdf_url = path(
            "pdf/<int:batch_number>/",
            self.admin_site.admin_view(self.export_pdf),
            name="reservations_reservation_pdf",
        )
        return [pdf_url] + urls

    def changelist_view(self, request, extra_context=None):
        context = {"stats": reservation_stats_service.get_stats()}
        if extra_context is not None:
            context.update(extra_context)
        return super().changelist_view(request, extra_context=context)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def delete_model(self, request, obj):
        reservation_service.cancel(reservation_id=obj.pk)

    def export_pdf(self, request, batch_number):
        try:
            pdf = reservation_pdf_service.render_batch(batch_number=batch_number)
        except NotFoundError:
            raise Http404("Batch not found.")
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="turnus{batch_number}.pdf"'
        return response

    @admin.action(description="Označit jako zaplacené")
    def mark_paid(self, request, queryset):
        done = 0
        for reservation in queryset:
            try:
                reservation_service.mark_paid(reservation_id=reservation.pk)
                done += 1
            except ApplicationError as error:
                self.message_user(request, f"{reservation}: {error.message}", level=messages.WARNING)
        self.message_user(request, f"Označeno jako zaplacené: {done}", level=messages.SUCCESS)

    @admin.action(description="Zrušit rezervaci")
    def cancel_reservations(self, request, queryset):
        done = 0
        for reservation in queryset:
            try:
                reservation_service.cancel(reservation_id=reservation.pk)
                done += 1
            except ApplicationError as error:
                self.message_user(request, f"{reservation}: {error.message}", level=messages.WARNING)
        self.message_user(request, f"Zrušeno rezervací: {done}", level=messages.SUCCESS)

    @admin.display(description="Fotka")
    def photo_link(self, obj):
        if not obj.photo:
            return "-"
        return format_html('<a href="{}" target="_blank">Fotka</a>', obj.photo.url)

    @admin.display(description="Jméno", ordering="surname")
    def full_name(self, obj):
        return f"{obj.name} {obj.surname}"

    @admin.display(description="Telefon", ordering="billing_information__phone")
    def phone(self, obj):
        return obj.billing_information.phone

    @admin.display(description="Fakulta", ordering="faculty__faculty_abbrev")
    def faculty_abbrev(self, obj):
        return obj.faculty.faculty_abbrev

    @admin.display(description="Turnus", ordering="batch__number")
    def batch_number(self, obj):
        return obj.batch.number

    @admin.display(description="Stav")
    def state(self, obj):
        if obj.is_substitute:
            return "Náhradník"
        if obj.is_paid:
            return "Zaplaceno"
        return "Nezaplaceno"

    @admin.display(description="Fakturační údaje")
    def billing_address(self, obj):
        billing = obj.billing_information
        return f"{billing.street}, {billing.postal_code} {billing.city}, {billing.country}, tel. {billing.phone}"
