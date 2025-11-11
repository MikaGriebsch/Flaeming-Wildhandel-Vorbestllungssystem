from allauth.account.forms import ResetPasswordForm
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.views.generic import TemplateView
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from users.models import User
from users.serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False, methods=["get"])
    def me(self, request):
        user = request.user
        if not user.is_authenticated:
            return Response({"detail": "Authentication credentials were not provided."}, status=401)
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "users/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        registrations = (
            self.request.user.offer_registrations.select_related("offer").order_by("-erstellt_at")
        )
        total_quantity = registrations.aggregate(total=Sum("menge"))["total"] or 0
        context.update(
            {
                "registrations": registrations,
                "total_orders": registrations.count(),
                "total_quantity": total_quantity,
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        if "send_password_reset" in request.POST:
            form = ResetPasswordForm({"email": request.user.email})
            if form.is_valid():
                form.save(request=request)
                messages.success(request, "Wir haben dir eine E-Mail zum Zurücksetzen deines Passworts geschickt.")
            else:
                messages.error(request, "Die Passwort-Zurücksetzung konnte nicht gestartet werden. Versuch es später erneut.")
        return super().get(request, *args, **kwargs)
