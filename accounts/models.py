from django.db import models
from django.contrib.auth.models import User

class UserOTP(models.Model):
    owners = models.ManyToManyField(User, related_name="userotp_owners")
    otp = models.IntegerField()  # Keep the same name used in views.py
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{', '.join(user.username for user in self.owners.all())} - {self.otp}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plain_password = models.CharField(max_length=128, blank=True)


class Event(models.Model):
    owners = models.ManyToManyField(User, related_name="event_owners")  # Changed related_name to avoid clash
    title = models.CharField(max_length=200)  # Event title
    description = models.TextField(blank=True)  # Optional event details
    event_date = models.DateTimeField()  # When the event happens
    created_at = models.DateTimeField(auto_now_add=True)

    meeting_link = models.URLField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    registration_limit = models.PositiveIntegerField(null=True, blank=True)
    registration_end_time = models.DateTimeField(null=True, blank=True)

    registrants = models.ManyToManyField(User, related_name='registered_events', blank=True)

    def __str__(self):
        return self.title
