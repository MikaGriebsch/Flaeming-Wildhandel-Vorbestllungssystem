from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import CheckConstraint, Q, Sum, UniqueConstraint
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class OfferQuerySet(models.QuerySet):
    def active(self):
        now = timezone.now()
        return self.filter(bestell_start__lte=now, bestell_ende__gte=now)

    def upcoming(self):
        now = timezone.now()
        return self.filter(bestell_start__gt=now)


class Offer(models.Model):
    titel = models.CharField("Titel", max_length=200)
    slug = models.SlugField(unique=True, max_length=200, blank=True)
    beschreibung = models.TextField("Beschreibung", blank=True)
    bestell_start = models.DateTimeField("Bestellfenster ab")
    bestell_ende = models.DateTimeField("Bestellfenster bis")
    abhol_von = models.DateField("Abholung ab")
    abhol_bis = models.DateField("Abholung bis")
    limit_gesamt = models.PositiveIntegerField("Verfügbare Menge insgesamt")
    limit_pro_user = models.PositiveIntegerField("Maximal pro Kunde", null=True, blank=True)
    erstellt_am = models.DateTimeField(auto_now_add=True)
    aktualisiert_am = models.DateTimeField(auto_now=True)

    objects = OfferQuerySet.as_manager()

    class Meta:
        ordering = ["bestell_start", "titel"]
        verbose_name = "Angebot"
        verbose_name_plural = "Angebote"

    def __str__(self):
        return self.titel

    def clean(self):
        errors = {}
        if self.bestell_start and self.bestell_ende and self.bestell_start >= self.bestell_ende:
            errors["bestell_ende"] = "Das Ende des Bestellzeitraums muss nach dem Start liegen."
        if self.bestell_ende and self.abhol_von and self.bestell_ende.date() > self.abhol_von:
            errors["abhol_von"] = "Die Abholung darf erst nach dem Bestellzeitraum starten."
        if self.abhol_von and self.abhol_bis and self.abhol_von > self.abhol_bis:
            errors["abhol_bis"] = "Das Abholende muss nach dem Abholstart liegen."
        if self.limit_gesamt <= 0:
            errors["limit_gesamt"] = "Das Bestandslimit muss größer als 0 sein."
        if self.limit_pro_user is not None and self.limit_pro_user == 0:
            errors["limit_pro_user"] = "Das Limit pro Nutzer muss mindestens 1 betragen."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titel)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("offers:detail", kwargs={"slug": self.slug})

    def remaining_quantity(self, exclude_registration: Optional["Registration"] = None):
        qs = self.registrations.all()
        if exclude_registration and exclude_registration.pk:
            qs = qs.exclude(pk=exclude_registration.pk)
        reserved = qs.aggregate(total=Sum("menge")).get("total") or 0
        return max(self.limit_gesamt - reserved, 0)

    def is_within_order_window(self):
        now = timezone.now()
        return self.bestell_start <= now <= self.bestell_ende

    def next_reminder_dates(self):
        return ReminderWindow(self.abhol_von, self.abhol_bis)


class Registration(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="offer_registrations")
    offer = models.ForeignKey(Offer, on_delete=models.PROTECT, related_name="registrations")
    menge = models.PositiveIntegerField("Menge")
    zustimmung_verbindlich_at = models.DateTimeField("Verbindlich bestätigt am")
    erstellt_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["offer", "user__last_name", "user__postal_code"]
        verbose_name = "Bestellung"
        verbose_name_plural = "Bestellungen"
        constraints = [
            UniqueConstraint(fields=["user", "offer"], name="unique_registration_per_offer"),
            CheckConstraint(check=Q(menge__gte=1), name="registration_min_one"),
        ]

    def __str__(self):
        return f"{self.user.email} → {self.offer.titel} ({self.menge})"

    def clean(self):
        errors = {}
        if self.offer_id:
            if not self.offer.is_within_order_window():
                errors["offer"] = "Dieses Angebot kann aktuell nicht mehr vorbestellt werden."
            remaining = self.offer.remaining_quantity(exclude_registration=self if self.pk else None)
            if self.menge > remaining:
                errors["menge"] = f"Nur noch {remaining} Stück verfügbar."
            if self.offer.limit_pro_user is not None and self.menge > self.offer.limit_pro_user:
                errors["menge"] = f"Maximal {self.offer.limit_pro_user} Stück pro Person möglich."
        if self.user_id and self.offer_id:
            exists = (
                Registration.objects.filter(user=self.user, offer=self.offer)
                .exclude(pk=self.pk)
                .exists()
            )
            if exists:
                errors["user"] = "Du hast dieses Angebot bereits verbindlich bestellt."
        if errors:
            raise ValidationError(errors)

    @transaction.atomic
    def confirm(self):
        self.zustimmung_verbindlich_at = timezone.now()
        self.full_clean()
        self.save()
        Consent.objects.create(
            user=self.user,
            offer=self.offer,
            typ=Consent.Type.VERBINDLICH,
            text_version=ConsentTexts.verbindlichkeit(self.offer)
        )


class Consent(models.Model):
    class Type(models.TextChoices):
        VERBINDLICH = "verbindlichkeit", "Verbindlichkeit"
        NEWSLETTER = "newsletter", "Newsletter"
        AGB = "agb", "AGB"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="consents")
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name="consents", null=True, blank=True)
    typ = models.CharField(max_length=32, choices=Type.choices)
    timestamp = models.DateTimeField(auto_now_add=True)
    text_version = models.TextField()

    class Meta:
        verbose_name = "Einwilligung"
        verbose_name_plural = "Einwilligungen"

    def __str__(self):
        return f"{self.get_typ_display()} ({self.user.email})"


class EmailLog(models.Model):
    class Typ(models.TextChoices):
        VERIFY = "verify", "Verifizierung"
        CONFIRM = "confirm", "Bestätigung"
        REMINDER_PRE = "reminder_pre", "Erinnerung vor Abholung"
        REMINDER_START = "reminder_start", "Erinnerung Abholbeginn"

    offer = models.ForeignKey(Offer, null=True, blank=True, on_delete=models.SET_NULL, related_name="email_logs")
    registration = models.ForeignKey(Registration, null=True, blank=True, on_delete=models.SET_NULL, related_name="email_logs")
    empfaenger = models.EmailField()
    typ = models.CharField(max_length=32, choices=Typ.choices)
    timestamp = models.DateTimeField(auto_now_add=True)
    zustellstatus = models.CharField(max_length=50, default="gesendet")
    nachricht_id = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "E-Mail-Protokoll"
        verbose_name_plural = "E-Mail-Protokolle"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.empfaenger} ({self.get_typ_display()})"


@dataclass
class ReminderWindow:
    abhol_von: date
    abhol_bis: date

    def pre_reminder_date(self) -> Optional[date]:
        if not self.abhol_von:
            return None
        return self.abhol_von - timedelta(days=2)

    def start_reminder_date(self) -> Optional[date]:
        return self.abhol_von


class ConsentTexts:
    @staticmethod
    def verbindlichkeit(offer: Offer) -> str:
        start = offer.abhol_von.strftime("%d.%m.%Y")
        end = offer.abhol_bis.strftime("%d.%m.%Y")
        return (
            "Ich bestätige, dass meine Auswahl verbindlich ist. Eine Stornierung ist nach der Bestätigung "
            "nicht möglich. Das Produkt ist im Zeitraum "
            f"{start} bis {end} abholbereit und wird von mir innerhalb dieses Fensters abgeholt."
        )
