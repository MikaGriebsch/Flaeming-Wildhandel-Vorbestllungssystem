from datetime import timedelta
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from offers.models import Offer, Registration
from offers.services import HEADER, export_registrations_pdf, registration_rows
from users.models import User


class RegistrationRuleTests(TestCase):
    def setUp(self):
        self.now = timezone.now()

    def _create_offer(self, **kwargs):
        defaults = {
            "titel": "Wildwurst Paket",
            "bestell_start": self.now - timedelta(hours=1),
            "bestell_ende": self.now + timedelta(hours=1),
            "abhol_von": (self.now + timedelta(days=3)).date(),
            "abhol_bis": (self.now + timedelta(days=5)).date(),
            "limit_gesamt": 10,
        }
        defaults.update(kwargs)
        offer = Offer.objects.create(**defaults)
        return offer

    def _create_user(self, email="kunde@example.com"):
        return User.objects.create_user(email=email, password="testpass123")

    def test_overselling_is_blocked(self):
        offer = self._create_offer(limit_gesamt=5)
        first_user = self._create_user("a@example.com")
        second_user = self._create_user("b@example.com")

        Registration(user=first_user, offer=offer, menge=4).confirm()

        with self.assertRaises(ValidationError):
            Registration(user=second_user, offer=offer, menge=2).confirm()

    def test_limit_per_user_is_enforced(self):
        offer = self._create_offer(limit_gesamt=10, limit_pro_user=2)
        user = self._create_user()

        with self.assertRaises(ValidationError):
            Registration(user=user, offer=offer, menge=3).confirm()

    def test_registration_only_within_order_window(self):
        offer = self._create_offer(
            bestell_start=self.now - timedelta(days=3),
            bestell_ende=self.now - timedelta(days=1),
        )
        user = self._create_user()

        with self.assertRaises(ValidationError):
            Registration(user=user, offer=offer, menge=1).confirm()

    def test_pdf_export_uses_correct_column_order(self):
        offer = self._create_offer(limit_gesamt=3)
        user = self._create_user()
        Registration(user=user, offer=offer, menge=1).confirm()

        rows = list(registration_rows(offer.registrations.all().select_related("user", "offer")))
        self.assertEqual(len(rows[0]), len(HEADER))
        self.assertEqual(rows[0][0], 1)
        self.assertEqual(rows[0][1], offer.titel)
        self.assertEqual(rows[0][2], 1)

        response = export_registrations_pdf(offer)
        self.assertIn("vorbestellungen", response["Content-Disposition"])
        self.assertIn("application/pdf", response["Content-Type"])


class OfferRegistrationViewTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.offer = Offer.objects.create(
            titel="Wildwurst Paket",
            bestell_start=self.now - timedelta(hours=1),
            bestell_ende=self.now + timedelta(hours=1),
            abhol_von=(self.now + timedelta(days=3)).date(),
            abhol_bis=(self.now + timedelta(days=5)).date(),
            limit_gesamt=10,
        )
        self.user = User.objects.create_user(email="kunde@example.com", password="testpass123")
        self.user.email_verified_at = self.now
        self.user.save(update_fields=["email_verified_at"])
        Registration(user=self.user, offer=self.offer, menge=2).confirm()

    def test_validation_error_during_save_is_shown_on_form(self):
        self.client.force_login(self.user)
        url = reverse("offers:detail", kwargs={"slug": self.offer.slug})

        with patch.object(Registration, "confirm", side_effect=ValidationError({"menge": ["Nur noch 0 Stück verfügbar."]})):
            response = self.client.post(url, {"menge": 3})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nur noch 0 Stück verfügbar.")

    def test_detail_view_shows_total_remaining_quantity(self):
        self.client.force_login(self.user)
        url = reverse("offers:detail", kwargs={"slug": self.offer.slug})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("remaining", response.context)
        self.assertEqual(response.context["remaining"], self.offer.remaining_quantity())
