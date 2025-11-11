from allauth.account import app_settings


def account(_request):
    """Expose django-allauth app settings under the legacy `account` key."""
    return {"account": app_settings}
