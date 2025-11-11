from django import forms

from offers.models import Registration


class RegistrationForm(forms.ModelForm):
    consent_text = ""

    class Meta:
        model = Registration
        fields = ["menge"]

    def __init__(self, user, offer, *args, **kwargs):
        self.user = user
        self.offer = offer
        super().__init__(*args, **kwargs)
        current_quantity = self.instance.menge if self.instance.pk else 0
        exclude = self.instance if self.instance.pk else None
        remaining_additional = offer.remaining_quantity(exclude_registration=exclude)
        max_quantity = current_quantity + remaining_additional
        if offer.limit_pro_user:
            max_quantity = min(max_quantity, offer.limit_pro_user)
        max_quantity = max(max_quantity, current_quantity)

        min_quantity = current_quantity or 1
        widget_attrs = {"min": min_quantity}
        if max_quantity:
            widget_attrs["max"] = max_quantity
        self.fields["menge"].widget = forms.NumberInput(attrs=widget_attrs)
        self.fields["menge"].min_value = min_quantity

        if current_quantity:
            additional = max(0, max_quantity - current_quantity)
            if additional > 0:
                self.fields["menge"].help_text = (
                    f"Du hast derzeit {current_quantity} Stück reserviert. Noch {additional} zusätzliche Stück verfügbar."
                )
            else:
                self.fields["menge"].help_text = "Du hast bereits alle verfügbaren Stück reserviert."
        else:
            if max_quantity > 0:
                self.fields["menge"].help_text = f"Die maximale Anzahl, die Sie bestellen können, ist {max_quantity}."
            else:
                self.fields["menge"].help_text = "Aktuell keine Stück verfügbar."
        abhol_von = offer.abhol_von.strftime("%d.%m.%Y")
        abhol_bis = offer.abhol_bis.strftime("%d.%m.%Y")
        self.consent_text = (
            "Ich bestätige, dass meine Auswahl verbindlich ist. Eine Stornierung ist nach der Bestätigung nicht "
            f"möglich. Das Produkt ist im Zeitraum {abhol_von} bis {abhol_bis} abholbereit und wird von mir innerhalb dieses Fensters abgeholt."
        )

    def clean(self):
        cleaned_data = super().clean()
        menge = cleaned_data.get("menge")
        current_quantity = self.instance.menge if self.instance.pk else 0

        if not self.user.is_authenticated:
            raise forms.ValidationError("Bitte melde dich zuerst an.")
        if not self.user.email_verified_at:
            raise forms.ValidationError("Bitte bestätige zuerst deine E-Mail-Adresse.")
        if not self.offer.is_within_order_window():
            raise forms.ValidationError("Dieses Angebot kann derzeit nicht bestellt werden.")

        if self.instance.pk and menge is not None and menge < current_quantity:
            raise forms.ValidationError({"menge": "Du kannst deine Reservierung nur erhöhen, nicht verringern."})

        if menge:
            exclude = self.instance if self.instance.pk else None
            remaining_additional = self.offer.remaining_quantity(exclude_registration=exclude)
            max_quantity = current_quantity + remaining_additional
            if self.offer.limit_pro_user:
                max_quantity = min(max_quantity, self.offer.limit_pro_user)
            if menge > max_quantity:
                if current_quantity:
                    additional_available = max(0, max_quantity - current_quantity)
                    if additional_available <= 0:
                        message = "Es sind keine zusätzlichen Stück verfügbar."
                    else:
                        message = (
                            f"Du kannst höchstens {max_quantity} Stück reservieren. ({additional_available} zusätzliche Stück verfügbar.)"
                        )
                else:
                    message = (
                        "Es sind keine Stück mehr verfügbar." if max_quantity <= 0 else f"Du kannst höchstens {max_quantity} Stück reservieren."
                    )
                raise forms.ValidationError({"menge": message})
            if self.offer.limit_pro_user and menge > self.offer.limit_pro_user:
                raise forms.ValidationError({"menge": f"Maximal {self.offer.limit_pro_user} Stück pro Person möglich."})
        return cleaned_data

    def save(self, commit=True):
        registration = super().save(commit=False)
        registration.pk = self.instance.pk
        registration.user = self.user
        registration.offer = self.offer
        if commit:
            registration.confirm()
        return registration
