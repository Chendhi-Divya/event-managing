
from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User
from django import forms




class UserOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.IntegerField()  # keep the same name you used in views.py
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.otp}"
    

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plain_password = models.CharField(max_length=128, blank=True)


class Event(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Who owns the event
    title = models.CharField(max_length=200)  # Event title
    description = models.TextField(blank=True)  # Optional event details
    event_date = models.DateTimeField()  # When the event happens
    created_at = models.DateTimeField(auto_now_add=True)  # When event was created automatically
    registrants = models.ManyToManyField(User, related_name="registered_events", blank=True)

    meeting_link = models.URLField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    registration_limit = models.PositiveIntegerField(null=True, blank=True)
    registration_end_time = models.DateTimeField(null=True, blank=True)
    
    # Registrants ManyToMany field as needed
    registrants = models.ManyToManyField(User, related_name='registered_events', blank=True)
    def __str__(self):
        return self.title