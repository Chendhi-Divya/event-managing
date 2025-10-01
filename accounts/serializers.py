from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import Event
class SignupSerializer(serializers.Serializer):
    """
    Serializer for user signup with username, email, and password.
    Validates duplicates and creates user on successful validation.
    """
    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if User.objects.filter(username=attrs["username"]).exists():
            raise serializers.ValidationError({"username": "Username already taken."})
        if User.objects.filter(email=attrs["email"]).exists():
            raise serializers.ValidationError({"email": "Email already registered."})
        return attrs

    def create(self, validated_data):
        # Create user with encrypted password
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        # Add OTP generation logic here if needed
        return user


class VerifyOTPSerializer(serializers.Serializer):
    """
    Serializer to handle OTP verification inputs.
    """
    username = serializers.CharField()
    otp = serializers.CharField()


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    Validates username/password and sets authenticated user in validated data.
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs["username"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError("Invalid username or password.")
        if not user.is_active:
            raise serializers.ValidationError("Account not activated. Verify email first.")
        attrs["user"] = user
        return attrs
class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ["id", "title", "description", "event_date", "start_time", "status", "cancel_reason", "cancelled_at"]