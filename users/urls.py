from allauth.account import views as account_views
from django.urls import path
from django.views.generic import RedirectView

from users.views import ProfileView

app_name = "users"

urlpatterns = [
    path("register", RedirectView.as_view(pattern_name="users:register_form", permanent=False)),
    path("login", RedirectView.as_view(pattern_name="users:login_form", permanent=False)),
    path(
        "passwort-zuruecksetzen",
        RedirectView.as_view(pattern_name="users:password_reset_form", permanent=False),
    ),
    path("profil", RedirectView.as_view(pattern_name="users:profile", permanent=False)),
    path("logout", account_views.LogoutView.as_view(), name="logout"),
    path("register/", account_views.SignupView.as_view(), name="register_form"),
    path("login/", account_views.LoginView.as_view(), name="login_form"),
    path("verify/", account_views.EmailVerificationSentView.as_view(), name="verify"),
    path(
        "passwort-zuruecksetzen/",
        account_views.PasswordResetView.as_view(),
        name="password_reset_form",
    ),
    path("profil/", ProfileView.as_view(), name="profile"),
]
