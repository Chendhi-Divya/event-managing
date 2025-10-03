from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import UserProfile, Event
from .forms import EventForm
from django.utils.timezone import now
from django.core.mail import get_connection, EmailMessage
import random
from django.core.mail import send_mail
from django.http import JsonResponse
from django.http import HttpResponseForbidden
from rest_framework_simplejwt.tokens import RefreshToken
import json
from accounts.utils.jwt_auth import jwt_required
def home(request):
    return render(request, "home.html")

def api_token_login(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    try:
        body = json.loads(request.body)
    except:
        return JsonResponse({"detail": "Invalid JSON"}, status=400)

    email = body.get("email")
    password = body.get("password")

    try:
        user_obj = User.objects.get(email=email)
        username = user_obj.username
    except User.DoesNotExist:
        return JsonResponse({"detail": "User does not exist"}, status=400)

    user = authenticate(username=username, password=password)
    if not user:
        return JsonResponse({"detail": "Invalid credentials"}, status=401)

    refresh = RefreshToken.for_user(user)
    access = str(refresh.access_token)

    return JsonResponse({
        "access": access,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    })

@jwt_required
def dashboard(request):
    form = EventForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            # Save the event
            event = form.save(commit=False)
            event.owner = request.user
            event.save()
            event.owners.add(request.user)

            # Extract invitation emails from form
            invitation_emails = form.cleaned_data.get("invitation_emails", "")
            emails = [email.strip() for email in invitation_emails.split(",") if email.strip()]

            # 🔹 Print emails to console for debugging
            print("Invitation Emails from frontend:", emails)

            # Send invitation emails
            if emails:
                subject = f"Invitation to event: {event.title}"
                message = (
                    f"You are invited to the event '{event.title}' scheduled on {event.event_date}.\n\n"
                    f"Details:\n{event.description}\n\n"
                    f"Start Time: {event.start_time}\n"
                    f"End Time: {event.end_time}\n\n"
                    f"Meeting Link: {event.meeting_link}"
                )
                from_email = getattr(settings, "DEFAULT_FROM_EMAIL", settings.EMAIL_HOST_USER)

                try:
                    connection = get_connection(fail_silently=False)
                    email_messages = [
                        EmailMessage(subject, message, from_email, [recipient])
                        for recipient in emails
                    ]
                    result = connection.send_messages(email_messages)
                    print("Email send result:", result)
                    if result > 0:
                        messages.success(request, "Event created and invitations sent.")
                    else:
                        messages.error(request, "Event created but emails could not be sent.")
                except Exception as e:
                    messages.error(request, f"Event created but failed to send invitations: {e}")
            else:
                messages.success(request, "Event created successfully.")

            return redirect('dashboard')
        else:
            messages.error(request, "Form validation failed.")
            print("Form errors:", form.errors)

    # GET request — fetch upcoming events
    today = now().date()
    all_events = Event.objects.filter(event_date__gte=today).exclude(owners=request.user).order_by('event_date')
    my_events = Event.objects.filter(event_date__gte=today, owners=request.user).order_by('event_date')

    for event in all_events:
        event.start_time_str = event.start_time.strftime("%H:%M") if event.start_time else None
        event.end_time_str = event.end_time.strftime("%H:%M") if event.end_time else None

    for event in my_events:
        event.start_time_str = event.start_time.strftime("%H:%M") if event.start_time else None
        event.end_time_str = event.end_time.strftime("%H:%M") if event.end_time else None

    return render(request, "accounts/dashboard.html", {
        "form": form,
        "all_events": all_events,
        "my_events": my_events,
    })


@login_required
def add_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            event.owners.add(request.user)

            invitation_emails = form.cleaned_data.get('invitation_emails', '')
            emails = [email.strip() for email in invitation_emails.split(',') if email.strip()]

            if emails:
                subject = f"Invitation to event: {event.title}"
                message = (
                    f"You are invited to the event '{event.title}' scheduled on {event.event_date}.\n\n"
                    f"Details:\n{event.description}\n"
                )
                from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@yourdomain.com")

                try:
                    connection = get_connection(fail_silently=False)
                    email_messages = [
                        EmailMessage(subject, message, from_email, [recipient])
                        for recipient in emails
                    ]
                    connection.send_messages(email_messages)
                except Exception as e:
                    print(f"Error sending invitations: {e}")
                    messages.error(request, "Some invitations could not be sent. Please check the email addresses and SMTP settings.")

            messages.success(request, "Event added and invitations sent.")
            return redirect('my_events')
        else:
            messages.error(request, "There was an error creating the event.")
    else:
        form = EventForm()
    

    return render(request, 'add_event.html', {'form': form})


@login_required
def register_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    now = timezone.now()

    if request.method == "POST":
        # Check deadline
        if event.registration_deadline and now > event.registration_deadline:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.accepts('application/json'):
                return JsonResponse({'success': False, 'error': "Registration for this event is closed."})
            messages.error(request, "Registration for this event is closed.")
            return redirect('dashboard')

        # Check max participants
        if event.max_participants is not None and event.registrants.count() >= event.max_participants:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.accepts('application/json'):
                return JsonResponse({'success': False, 'error': "Registration limit reached for this event."})
            messages.error(request, "Registration limit reached for this event.")
            return redirect('dashboard')

        # Prevent duplicate registration
        if request.user not in event.registrants.all():
            event.registrants.add(request.user)

         
            # Email to participant
            if request.user.email:
                send_mail(
                    subject=f"Registration Confirmed: {event.title}",
                    message=f"You have successfully registered for {event.title}.\n"
                            f"Event Date: {event.event_date}\n\nDetails: {event.description}",
                    from_email="noreply@eventmanager.com",
                    recipient_list=[request.user.email],
                    fail_silently=True,
                )

            # Email to organiser(s)
            organisers = [owner.email for owner in event.owners.all() if owner.email]
            if organisers:
                send_mail(
                    subject=f"New Registration for {event.title}",
                     message=(
                        f"{request.user.username} ({request.user.email}) has registered for your event {event.title}."
                    ),
                                from_email="noreply@eventmanager.com",
                    recipient_list=organisers,
                    fail_silently=True,
                )

        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.accepts('application/json'):
            return JsonResponse({'success': True})

        messages.success(request, "You have registered successfully.")
        return redirect('registration_success', event_id=event.id)

    # Fallback for non-POST requests
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

            # Generate JWT token
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            response = redirect('dashboard')  # Redirect after OTP verification

            # Set JWT in cookie
            response.set_cookie(
                key="jwt_token",
                value=access_token,
                httponly=True,
                secure=False,    # Change to True in production with HTTPS
                samesite="Lax",
                max_age=3600 
            )

            messages.success(request, "Account verified! Welcome to your dashboard.")
            return response
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, "accounts/verify_otp.html", {"registered_email": registered_email})

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        # Check if user exists
        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username
        except User.DoesNotExist:
            messages.error(request, "User does not exist — please sign up.")
            return render(request, "accounts/login.html")

        # Authenticate user
        user = authenticate(request, username=username, password=password)
        if user:
            auth_login(request, user)

            # Generate JWT token
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            response = redirect("dashboard")  # Redirect after login

            # Set JWT in cookie
            response.set_cookie(
                key="jwt_token",
                value=access_token,
                httponly=True,
                secure=False,    # Change to True in production with HTTPS
                samesite="Lax",
                max_age=3600
            )

            return response
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
            updated_event = form.save()

            # Get invitation emails as comma separated string from form
            invitation_emails = form.cleaned_data.get('invitation_emails', '')
            emails = [email.strip() for email in invitation_emails.split(',') if email.strip()]

            if emails:
                subject = f"Invitation to event: {updated_event.title}"
                message = (
                    f"You are invited to the event '{updated_event.title}' scheduled on {updated_event.event_date}.\n\n"
                    f"Details:\n{updated_event.description}\n\n"
                    f"Start Time: {updated_event.start_time}\n"
                    f"End Time: {updated_event.end_time}\n\n"
                    f"Meeting Link: {updated_event.meeting_link}"
                )
                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER)

                try:
                    connection = get_connection(fail_silently=False)
                    email_messages = [EmailMessage(subject, message, from_email, [email]) for email in emails]
                    connection.send_messages(email_messages)
                    messages.success(request, "Event updated and invitations sent.")
                except Exception as e:
                    messages.error(request, f"Event updated but invitations failed to send: {e}")
            else:
                messages.success(request, "Event updated successfully.")

            return redirect('my_events')
        else:
            messages.error(request, "Form validation failed.")
    else:
        form = EventForm(instance=event)

    return render(request, 'accounts/edit_event.html', {'form': form, 'event': event})

def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == "POST":
        event.delete()
        return redirect('my_events')
    return render(request, 'confirm_delete.html', {'event': event})

@login_required
def cancel_event(request, event_id):
    # Ensure the event exists and the current user is an owner
    event = get_object_or_404(Event, id=event_id, owners=request.user)

    # Update status
    event.status = "Cancelled"
    event.save()

    # Get participants
    participants = event.registrants.all()

    # Send cancellation emails
    for user in participants:
        if user.email:
            send_mail(
                subject=f"Event Cancelled: {event.title}",
                message=(
                    f"Dear {user.username},\n\n"
                    f"We regret to inform you that the event '{event.title}' scheduled on "
                    f"{event.event_date.strftime('%Y-%m-%d')} has been cancelled.\n\n"
                    f"Regards,\nEvent Manager"
                ),
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@eventmanager.com"),
                recipient_list=[user.email],
                fail_silently=True,
            )

    messages.success(request, "Event has been cancelled and participants notified.")
    return redirect("dashboard")
