from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.utils import timezone

from .models import UserProfile, Event
from .forms import EventForm

import random

def home(request):
    return render(request, "home.html")

def add_event(request):
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            return redirect('dashboard')  # or redirect to event list/detail
    else:
        form = EventForm()
    return render(request, 'accounts/add_event.html', {'form': form})




@login_required
def dashboard(request):
    # Events NOT created by current user
    outsider_events = Event.objects.exclude(user=request.user).order_by('event_date')

    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.user = request.user  # Assign logged-in user as creator
            event.save()
            return redirect('dashboard')
    else:
        form = EventForm()

    context = {
        'outsider_events': outsider_events,
        'form': form,
        'user': request.user
    }
    return render(request, "accounts/dashboard.html", context)


    

@login_required
def register_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    user = request.user
    if user not in event.registrants.all():
        event.registrants.add(user)
    return redirect('registration_success', event_id=event.id)  # <-- changed line

@login_required
def registration_success(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    return render(request, 'accounts/registration_success.html', {'event': event})


def signup(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "accounts/signup.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, "accounts/signup.html")
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, "accounts/signup.html")

        otp = generate_otp()
        request.session['signup_otp'] = otp
        request.session['signup_user'] = {
            'username': username,
            'email': email,
            'password': password
        }
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
        entered_otp = ''.join([request.POST.get(f'otp{i}', '') for i in range(1, 7)])
        session_otp = request.session.get('signup_otp')

        if entered_otp == session_otp:
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password']
            )
            user.save()

            UserProfile.objects.create(user=user, plain_password=user_data['password'])

            del request.session['signup_otp']
            del request.session['signup_user']

            auth_login(request, user)

            messages.success(request, "Account verified! Welcome to your dashboard.")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid OTP. Please try again.")
            return render(request, "accounts/verify_otp.html", {"registered_email": registered_email})

    return render(request, "accounts/verify_otp.html", {"registered_email": registered_email})


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")  # get email from form
        password = request.POST.get("password")

        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username
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


@login_required
def logout_view(request):
    auth_logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")


def generate_otp():
    """Generate a 6-digit OTP as string."""
    return str(random.randint(100000, 999999))


def send_otp_email(email, otp):
    subject = "Your OTP for Event Manager"
    message = f"Your OTP is: {otp}. It is valid for 10 minutes."
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list, fail_silently=False)


def event_list(request):
    events = Event.objects.order_by('event_date')
    return render(request, "accounts/event_list.html", {"events": events})

def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    return render(request, "accounts/event_detail.html", {"event": event})

@login_required
def my_events(request):
    user_events = Event.objects.filter(user=request.user).order_by('event_date')

    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.user = request.user  # assign the current user as the creator
            event.save()
            return redirect('my_events')
    else:
        form = EventForm()

    context = {
        'user_events': user_events,
        'form': form,
        'user': request.user
    }
    return render(request, "accounts/my_events.html", context)
def register_for_event(request, event_id):
    event = Event.objects.get(id=event_id)
    now = timezone.now()
    
    if event.registration_end_time and now > event.registration_end_time:
        # Registration closed
        messages.error(request, "Registration for this event is closed.")
        return redirect('dashboard')
    
    if event.registration_limit is not None and event.registrants.count() >= event.registration_limit:
        # Limit reached
        messages.error(request, "Registration limit reached for this event.")
        return redirect('dashboard')
    
    # Otherwise, proceed with registration
    event.registrants.add(request.user)
    messages.success(request, "You have successfully registered.")
    return redirect('dashboard')