from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from users.forms import UserChangeForm, UserCreationForm
from users.models import User

admin.site.enable_nav_sidebar = False


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    model = User
    list_display = (
        "email",
        "first_name",
        "last_name",
        "postal_code",
        "city",
        "email_verified_at",
        "is_staff",
        "is_active",
    )
    list_filter = ("is_staff", "is_active", "email_verified_at", "city")
    search_fields = ("email", "first_name", "last_name", "postal_code")
    ordering = ("email",)
    readonly_fields = ("email_verified_at", "date_joined", "last_login", "created", "modified")

    fieldsets = (
        (None, {"fields": ("email", "password")} ),
        (_("Persönliche Daten"), {"fields": ("first_name", "last_name", "street", "house_number", "postal_code", "city")}),
        (_("Status"), {"fields": ("email_verified_at", "is_active", "is_staff", "is_superuser")} ),
        (_("Bereiche"), {"fields": ("groups", "user_permissions")} ),
        (_("Wichtige Zeitstempel"), {"fields": ("date_joined", "last_login", "created", "modified")} ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "street",
                    "house_number",
                    "postal_code",
                    "city",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_superuser",
                    "is_active",
                    "groups",
                ),
            },
        ),
    )
