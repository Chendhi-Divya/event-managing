from django.db import models
from django.contrib.auth.models import User


class UserOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.otp}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plain_password = models.CharField(max_length=128, blank=True)

    def __str__(self):
        return self.user.username

class Event(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_events")  
    owners = models.ManyToManyField(User, related_name="my_events", blank=True)
    registrants = models.ManyToManyField(User, related_name="registered_events", blank=True)  # <-- Added
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    event_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    meeting_link = models.URLField(blank=True)
    registration_deadline = models.DateTimeField(null=True, blank=True)
    is_admin_event = models.BooleanField(default=False)
    invitation_emails = models.TextField(
        blank=True,
        null=True,
        help_text="Comma-separated email addresses for invitations"
    )

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['event_date']
