from django.contrib import admin, messages

from offers.models import Consent, EmailLog, Offer, Registration
from offers.services import (
    export_registrations_csv,
    export_registrations_excel,
    export_registrations_pdf,
)


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = (
        "titel",
        "bestell_start",
        "bestell_ende",
        "abhol_von",
        "abhol_bis",
        "limit_gesamt",
        "limit_pro_user",
        "remaining",
    )
    search_fields = ("titel", "beschreibung")
    prepopulated_fields = {"slug": ("titel",)}
    list_filter = ("bestell_start", "abhol_von")
    actions = ["export_vorbestellungen_csv", "export_vorbestellungen_excel", "export_vorbestellungen_pdf"]

    @admin.display(description="Verfügbar")
    def remaining(self, obj):
        return obj.remaining_quantity()

    def _single_offer_action(self, request, queryset, exporter):
        if queryset.count() != 1:
            self.message_user(request, "Bitte genau ein Angebot wählen.", level=messages.ERROR)
            return None
        offer = queryset.first()
        return exporter(offer)

    @admin.action(description="Vorbestellungen als CSV exportieren")
    def export_vorbestellungen_csv(self, request, queryset):
        return self._single_offer_action(request, queryset, export_registrations_csv)

    @admin.action(description="Vorbestellungen als Excel exportieren")
    def export_vorbestellungen_excel(self, request, queryset):
        return self._single_offer_action(request, queryset, export_registrations_excel)

    @admin.action(description="Vorbestellungen als PDF exportieren")
    def export_vorbestellungen_pdf(self, request, queryset):
        return self._single_offer_action(request, queryset, export_registrations_pdf)


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = (
        "offer",
        "user",
        "menge",
        "zustimmung_verbindlich_at",
        "erstellt_at",
    )
    search_fields = ("offer__titel", "user__email", "user__last_name")
    list_filter = ("offer", "zustimmung_verbindlich_at")
    autocomplete_fields = ("offer", "user")
    ordering = ("offer", "user__last_name")


@admin.register(Consent)
class ConsentAdmin(admin.ModelAdmin):
    list_display = ("user", "offer", "typ", "timestamp")
    search_fields = ("user__email", "offer__titel")
    list_filter = ("typ", "timestamp")


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ("empfaenger", "typ", "offer", "timestamp", "zustellstatus")
    search_fields = ("empfaenger", "offer__titel")
    list_filter = ("typ", "timestamp")
    readonly_fields = ("timestamp",)
