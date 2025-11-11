from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView, TemplateView, View

from offers.forms import RegistrationForm
from offers.models import Offer, Registration
from offers.services import send_registration_confirmation


class OfferListView(ListView):
    model = Offer
    template_name = "offers/offer_list.html"
    context_object_name = "angebote"

    def get_queryset(self):
        now = timezone.now()
        return Offer.objects.filter(bestell_ende__gte=now).order_by("bestell_start")
class OfferRegistrationView(View):
    template_name = "offers/offer_detail.html"

    def get_offer(self):
        return get_object_or_404(Offer, slug=self.kwargs["slug"])

    def get(self, request, *args, **kwargs):
        offer = self.get_offer()
        registration_instance = None
        form = None
        already_registered = False

        if request.user.is_authenticated:
            try:
                registration_instance = Registration.objects.get(user=request.user, offer=offer)
                already_registered = True
                form = RegistrationForm(request.user, offer, instance=registration_instance)
            except Registration.DoesNotExist:
                form = RegistrationForm(request.user, offer)
        else:
            form = None
        return render(
            request,
            self.template_name,
            {
                "offer": offer,
                "form": form,
                "already_registered": already_registered,
                "existing_registration": registration_instance,
                "remaining": offer.remaining_quantity(),
                "needs_login": not request.user.is_authenticated,
                "needs_verification": request.user.is_authenticated and request.user.email_verified_at is None,
            },
        )

    def post(self, request, *args, **kwargs):
        offer = self.get_offer()
        if not request.user.is_authenticated:
            login_url = f"{reverse('login')}?next={request.path}"
            return redirect(login_url)
        if request.user.email_verified_at is None:
            messages.error(request, "Bitte bestätige zuerst deine E-Mail-Adresse.")
            return redirect("verify")

        existing_registration = Registration.objects.filter(user=request.user, offer=offer).first()
        original_quantity = existing_registration.menge if existing_registration else None
        form = RegistrationForm(request.user, offer, request.POST, instance=existing_registration)
        if form.is_valid():
            new_quantity = form.cleaned_data["menge"]
            if existing_registration and new_quantity == original_quantity:
                messages.info(request, "Es gab keine Änderungen an deiner Reservierung.")
                return redirect("offers:success", slug=offer.slug)

            try:
                registration = form.save()
            except ValidationError as exc:
                # Surface late validation issues (e.g. concurrent stock changes) back to the form.
                if hasattr(exc, "message_dict"):
                    for field, error_list in exc.message_dict.items():
                        target = field if field in form.fields else None
                        for error in error_list:
                            form.add_error(target, error)
                else:
                    form.add_error(None, exc.message)
            else:
                if existing_registration is None:
                    send_registration_confirmation(registration)
                    messages.success(request, "Vielen Dank! Deine verbindliche Reservierung wurde gespeichert.")
                else:
                    send_registration_confirmation(registration)
                    messages.success(request, "Deine Reservierung wurde aktualisiert.")
                return redirect("offers:success", slug=offer.slug)

        return render(
            request,
            self.template_name,
            {
                "offer": offer,
                "form": form,
                "already_registered": existing_registration is not None,
                "existing_registration": existing_registration,
                "remaining": offer.remaining_quantity(),
                "needs_login": False,
                "needs_verification": False,
            },
        )


class OfferSuccessView(TemplateView):
    template_name = "offers/registration_success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        offer = get_object_or_404(Offer, slug=kwargs["slug"])
        context["offer"] = offer
        context["abhol_von"] = offer.abhol_von.strftime("%d.%m.%Y")
        context["abhol_bis"] = offer.abhol_bis.strftime("%d.%m.%Y")
        return context
