from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from allauth.account.forms import SignupForm

from users.models import User


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Passwort", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Passwort bestätigen", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "street",
            "house_number",
            "postal_code",
            "city",
        )

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Die Passwörter stimmen nicht überein.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(label="Passwort")

    class Meta:
        model = User
        fields = (
            "email",
            "password",
            "first_name",
            "last_name",
            "street",
            "house_number",
            "postal_code",
            "city",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
        )

    def clean_password(self):
        return self.initial.get("password")


class UserSignupForm(SignupForm):
    first_name = forms.CharField(label="Vorname", max_length=150)
    last_name = forms.CharField(label="Nachname", max_length=150)
    street = forms.CharField(label="Straße", max_length=150)
    house_number = forms.CharField(label="Hausnummer", max_length=20)
    postal_code = forms.CharField(label="PLZ", max_length=10)
    city = forms.CharField(label="Ort", max_length=150)

    field_order = (
        "email",
        "first_name",
        "last_name",
        "street",
        "house_number",
        "postal_code",
        "city",
        "password1",
        "password2",
    )

    def signup(self, request, user):
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name = self.cleaned_data["last_name"].strip()
        user.street = self.cleaned_data["street"].strip()
        user.house_number = self.cleaned_data["house_number"].strip()
        user.postal_code = self.cleaned_data["postal_code"].strip()
        user.city = self.cleaned_data["city"].strip()
        user.save(update_fields=[
            "first_name",
            "last_name",
            "street",
            "house_number",
            "postal_code",
            "city",
        ])
        return user
