from allauth.account.signals import email_confirmed
from django.dispatch import receiver


@receiver(email_confirmed)
def user_email_confirmed(request, email_address, **kwargs):
    user = email_address.user
    if user:
        user.mark_email_verified()
