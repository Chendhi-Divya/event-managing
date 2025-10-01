from functools import wraps
from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


def jwt_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        token = request.COOKIES.get("jwt_token")  # ✅ Get JWT token from cookie

        if not token:
            return JsonResponse({"detail": "Authentication credentials were not provided."}, status=401)

        try:
            jwt_authenticator = JWTAuthentication()
            validated_token = jwt_authenticator.get_validated_token(token)
            user = jwt_authenticator.get_user(validated_token)
            request.user = user
        except (InvalidToken, TokenError):
            return JsonResponse({"detail": "Invalid or expired token."}, status=401)

        return view_func(request, *args, **kwargs)

    return wrapper
