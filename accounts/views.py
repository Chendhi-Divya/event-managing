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
from django.http import JsonResponse
from django.http import HttpResponseForbidden


def home(request):
    return render(request, "home.html")


@login_required(login_url='/login/')
def dashboard(request):
    form = EventForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            event = form.save(commit=False)  # Don't save yet
            event.owner = request.user       # Set owner before saving
            event.save()                     # Now save
            event.owners.add(request.user)   # Add to owners list
            messages.success(request, "Event created successfully.")
            return redirect('dashboard')
        else:
            print("Form errors:", form.errors)

    all_events = Event.objects.exclude(owners=request.user).order_by('event_date')

    # Ensure times are strings for display
    for event in all_events:
        event.start_time_str = event.start_time.strftime("%H:%M") if event.start_time else None
        event.end_time_str = event.end_time.strftime("%H:%M") if event.end_time else None

    return render(request, "accounts/dashboard.html", {
        "form": form,
        "all_events": all_events
    })

def add_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            event.owners.add(request.user)
            messages.success(request, "Event added successfully.")
            return redirect('my_events')
        else:
            print(form.errors)
    else:
        form = EventForm()

    return render(request, 'add_event.html', {'form': form})


@login_required
def register_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    now = timezone.now()

    if request.method == "POST":
        if event.registration_deadline and now > event.registration_deadline:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.accepts('application/json'):
                return JsonResponse({'success': False, 'error': "Registration for this event is closed."})
            messages.error(request, "Registration for this event is closed.")
            return redirect('dashboard')

        if event.max_participants is not None and event.registrants.count() >= event.max_participants:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.accepts('application/json'):
                return JsonResponse({'success': False, 'error': "Registration limit reached for this event."})
            messages.error(request, "Registration limit reached for this event.")
            return redirect('dashboard')

        # Add user to registrants only if not already registered
        if request.user not in event.registrants.all():
            event.registrants.add(request.user)

        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.accepts('application/json'):
            return JsonResponse({'success': True})

        messages.success(request, "Registered for event successfully.")
        return redirect('registration_success', event_id=event.id)

    # For non-POST requests, redirect to event details
    return redirect('event_detail', event_id=event.id)


@login_required
def registration_success(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    return render(request, 'accounts/registration_success.html', {'event': event})


@login_required
def my_events(request):
    my_events = Event.objects.filter(owners=request.user).order_by('event_date')

    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.is_admin_event = False
            event.save()
            event.owners.add(request.user)
            messages.success(request, "Event added successfully.")
            return redirect('my_events')
    else:
        form = EventForm()

    return render(request, 'accounts/my_events.html', {
        'my_events': my_events,
        'form': form,
    })


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
            'password': password,
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
            UserProfile.objects.create(user=user, plain_password=user_data['password'])
            del request.session['signup_otp']
            del request.session['signup_user']
            auth_login(request, user)
            messages.success(request, "Account verified! Welcome to your dashboard.")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid OTP. Please try again.")
    return render(request, "accounts/verify_otp.html", {"registered_email": registered_email})


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
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


@login_required
def logout_view(request):
    auth_logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")


def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp_email(email, otp):
    subject = "Your OTP for Event Manager"
    message = f"Your OTP is: {otp}. It is valid for 5 minutes."
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list, fail_silently=False)


@login_required
def event_list(request):
    events = Event.objects.filter(is_admin_event=True).order_by('event_date')
    return render(request, "accounts/event_list.html", {"events": events})


@login_required
def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    return render(request, 'accounts/event_detail.html', {'event': event})



@login_required
def registered_events(request):
    events = Event.objects.filter(registrants=request.user)
    return render(request, 'accounts/registered_events.html', {'events': events})

@login_required
def unregister_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.registrants.remove(request.user)
    return redirect('registered_events')

def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == "POST":
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            return redirect('my_events')
    else:
        form = EventForm(instance=event)

    return render(request, 'accounts/edit_event.html', {'form': form, 'event': event})

def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == "POST":
        event.delete()
        return redirect('my_events')
    return render(request, 'confirm_delete.html', {'event': event})
