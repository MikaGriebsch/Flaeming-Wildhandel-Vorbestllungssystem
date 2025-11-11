from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from utils.models import BaseModel


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Eine E-Mail-Adresse ist erforderlich")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def get_by_natural_key(self, email):
        """Look up users case-insensitively by email for auth backends."""
        return self.get(**{f"{self.model.USERNAME_FIELD}__iexact": self.normalize_email(email)})

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser muss is_staff=True haben.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser muss is_superuser=True haben.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, BaseModel, PermissionsMixin):
    email = models.EmailField(_("E-Mail-Adresse"), unique=True)
    first_name = models.CharField(_("Vorname"), max_length=150, blank=True)
    last_name = models.CharField(_("Nachname"), max_length=150, blank=True)
    street = models.CharField(_("Straße"), max_length=150, blank=True)
    house_number = models.CharField(_("Hausnummer"), max_length=20, blank=True)
    postal_code = models.CharField(_("PLZ"), max_length=10, blank=True)
    city = models.CharField(_("Ort"), max_length=150, blank=True)
    email_verified_at = models.DateTimeField(_("E-Mail bestätigt am"), null=True, blank=True)
    is_staff = models.BooleanField(
        _("Mitarbeiterstatus"),
        default=False,
        help_text=_("Legt fest, ob der Benutzer sich im Admin anmelden darf."),
    )
    is_active = models.BooleanField(
        _("Aktiv"),
        default=True,
        help_text=_("Legt fest, ob dieser Benutzer als aktiv behandelt werden soll."),
    )
    date_joined = models.DateTimeField(_("Registriert am"), default=timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    data = UserManager()
    objects = UserManager()

    class Meta(BaseModel.Meta):
        verbose_name = _("Benutzer")
        verbose_name_plural = _("Benutzer")

    def __str__(self):
        return self.get_full_name() or self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name or self.email

    @property
    def address(self):
        if self.street and self.house_number and self.postal_code and self.city:
            return f"{self.street} {self.house_number}, {self.postal_code} {self.city}"
        return ""

    def mark_email_verified(self):
        if not self.email_verified_at:
            self.email_verified_at = timezone.now()
            self.save(update_fields=["email_verified_at"])

    def send_templated_email(self, subject, template_name, context=None):
        context = context or {}
        context.setdefault("user", self)
        text_body = render_to_string(f"email/{template_name}.txt", context)
        html_body = render_to_string(f"email/{template_name}.html", context)
        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            to=[self.email],
        )
        message.attach_alternative(html_body, "text/html")
        message.send()
