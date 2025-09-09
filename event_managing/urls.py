from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from accounts import views  # Import your accounts app views

# Home view (can keep inline or move to views.py)
def home(request):
    return render(request, "home.html")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),

    # Use actual view functions to handle signup/login/verify_otp logic properly
    path("signup/", views.signup, name="signup"),
    path("login/", views.login_view, name="login"),
    path("verify-otp/", views.verify_otp, name="verify_otp"),

    # If you have API endpoints in accounts/urls.py for JWT or REST APIs
    path("api/auth/", include("accounts.urls")),
]
