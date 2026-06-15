from dataclasses import dataclass

from rest_framework import serializers

from .models import User


@dataclass(frozen=True)
class AuthSession:
    """Tokens and user of a successful login or refresh."""

    user: User
    access: str
    refresh: str | None


class LoginRequestSerializer(serializers.Serializer):
    """Body of the login request."""

    username = serializers.CharField()
    password = serializers.CharField(style={"input_type": "password"})


class UserResponseSerializer(serializers.Serializer):
    """The logged-in user."""

    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
