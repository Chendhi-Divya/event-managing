from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from .models import UserProfile
from .models import Event
from .forms import EventForm
from django.contrib.auth.views import LoginView

import random


def home(request):
    return render(request, "home.html")


@login_required
def dashboard(request):
    events = Event.objects.order_by('event_date')
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            return redirect('dashboard')
    else:
        form = EventForm()
    return render(request, 'events/dashboard.html', {
        'events': events,
        'form': form,
        'user': request.user
    })

@login_required
def register_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.user in event.registrants.all():
        event.registrants.remove(request.user)  # Unregister
    else:
        event.registrants.add(request.user)      # Register
    return redirect('dashboard')


def signup(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        # Password match check
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "accounts/signup.html")

        # Unique username/email check
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, "accounts/signup.html")
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, "accounts/signup.html")

        # Generate OTP and store in session
        otp = generate_otp()
        request.session['signup_otp'] = otp
        request.session['signup_user'] = {
            'username': username,
            'email': email,
            'password': password
        }

        # Send OTP to email
        send_otp_email(email, otp)
        messages.info(request, f"OTP sent to {email}. Please verify.")

        return redirect('verify_otp')

    return render(request, "accounts/signup.html")



def verify_otp(request):
    user_data = request.session.get('signup_user')
    if not user_data:
        messages.error(request, "Session expired or invalid. Please sign up again.")
        return redirect('signup')

    registered_email = user_data.get('email', '')

    if request.method == "POST":
        # Combine 6 separate OTP inputs into one string
        entered_otp = ''.join([request.POST.get(f'otp{i}', '') for i in range(1, 7)])
        session_otp = request.session.get('signup_otp')

        if entered_otp == session_otp:
            # OTP is correct; create user and clear session

            # Create Django user
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password']
            )
            user.save()

            # Create UserProfile with plain password if needed (note: for learning only, not production)
            UserProfile.objects.create(user=user, plain_password=user_data['password'])

            # Clear session data
            del request.session['signup_otp']
            del request.session['signup_user']

            # Log in the user immediately
            auth_login(request, user)

            messages.success(request, "Account verified! Welcome to your dashboard.")
            return redirect('dashboard')

        else:
            messages.error(request, "Invalid OTP. Please try again.")
            return render(request, "accounts/verify_otp.html", {"registered_email": registered_email})

    # GET request: show the OTP page
    return render(request, "accounts/verify_otp.html", {"registered_email": registered_email})




def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")  # get email from form
        password = request.POST.get("password")

        # Check if user with given email exists
        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username  # get username for authentication
        except User.DoesNotExist:
            messages.error(request, "User does not exist, please sign in")
            return render(request, "accounts/login.html")

        user = authenticate(username=username, password=password)
        if user:
            auth_login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid password, please try again.")
            return render(request, "accounts/login.html")

    return render(request, "accounts/login.html")




def logout_view(request):
    auth_logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")


def generate_otp():
    """Generate a 6-digit OTP as a string."""
    return str(random.randint(100000, 999999))


def send_otp_email(email, otp):
    subject = "Your OTP for Event Manager"
    message = f"Your OTP is: {otp}. It is valid for 10 minutes."
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list, fail_silently=False)



def event_list(request):
    events = Event.objects.order_by('event_date')
    return render(request, "events/event_list.html", {"events": events})

def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    return render(request, "events/event_detail.html", {"event": event})


def register_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    user = request.user
    if user in event.registrants.all():
        event.registrants.remove(user)  # Unregister
    else:
        event.registrants.add(user)     # Register
    return redirect('event_detail', event_id=event.id)