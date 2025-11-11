from django.urls import path
from django.views.generic import RedirectView

from offers.views import OfferListView, OfferRegistrationView, OfferSuccessView

app_name = "offers"

urlpatterns = [
    path("", OfferListView.as_view(), name="home"),
    path("angebote", RedirectView.as_view(pattern_name="offers:list", permanent=False)),
    path("angebote/", OfferListView.as_view(), name="list"),
    path("angebote/<slug:slug>", RedirectView.as_view(pattern_name="offers:detail", permanent=False)),
    path("angebote/<slug:slug>/", OfferRegistrationView.as_view(), name="detail"),
    path(
        "angebote/<slug:slug>/danke",
        RedirectView.as_view(pattern_name="offers:success", permanent=False),
    ),
    path("angebote/<slug:slug>/danke/", OfferSuccessView.as_view(), name="success"),
]
