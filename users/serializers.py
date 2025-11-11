from rest_framework import serializers

from users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "street",
            "house_number",
            "postal_code",
            "city",
            "email_verified_at",
        )
        read_only_fields = ("id",)
