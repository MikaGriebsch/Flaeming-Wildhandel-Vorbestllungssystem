from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from offers.models import EmailLog, Registration
from offers.services import send_reminder_email


class Command(BaseCommand):
    help = "Verschickt Erinnerungs-Mails vor und zum Start des Abholfensters."

    def handle(self, *args, **options):
        today = timezone.localdate()
        pre_reminder_date = today + timedelta(days=2)

        pre_registrations = Registration.objects.select_related("offer", "user").filter(
            offer__abhol_von=pre_reminder_date
        )
        start_registrations = Registration.objects.select_related("offer", "user").filter(
            offer__abhol_von=today
        )

        sent_count = 0

        for registration in pre_registrations:
            if not self._already_sent(registration, EmailLog.Typ.REMINDER_PRE):
                send_reminder_email(registration, EmailLog.Typ.REMINDER_PRE)
                sent_count += 1

        for registration in start_registrations:
            if not self._already_sent(registration, EmailLog.Typ.REMINDER_START):
                send_reminder_email(registration, EmailLog.Typ.REMINDER_START)
                sent_count += 1

        self.stdout.write(self.style.SUCCESS(f"{sent_count} Erinnerungs-Mails versendet."))

    @staticmethod
    def _already_sent(registration, reminder_type):
        return EmailLog.objects.filter(registration=registration, typ=reminder_type).exists()
