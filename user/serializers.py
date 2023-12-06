from django.contrib.auth import get_user_model

from djoser.serializers import UserSerializer as DjoserUserSerializer


class UserSerializer(DjoserUserSerializer):
    class Meta(DjoserUserSerializer.Meta):
        fields = ["id", "email", "username"]
        read_only_fields = None

    def create(self, validated_data: dict):
        """Create new user with encrypted password"""
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Update user with encrypted password"""
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)

        user.save()
        return user
