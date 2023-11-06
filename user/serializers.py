from rest_framework.serializers import ModelSerializer
from django.contrib.auth import get_user_model


class UserSerializer(ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "email", "username", "password", "is_staff"]
        read_only_fields = ["is_staff"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data: dict):
        """Create new user with encrypted password"""
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Update user with encypted password"""
        password = validated_data.pop("password", None)
        user = super().update(**validated_data)

        if password:
            user.set_password(password)

        user.save()
        return user
