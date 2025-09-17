from django import forms
from .models import Event


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title', 'meeting_link', 'start_time', 'end_time',
            'registration_limit', 'registration_end_time', 'event_date', 'description'
        ]
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'registration_end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'event_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned_data = super().clean()

        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')
        reg_end = cleaned_data.get('registration_end_time')
        limit = cleaned_data.get('registration_limit')

        # Validate start_time is before end_time
        if start and end and start >= end:
            self.add_error('end_time', 'End time must be after start time.')

        # Validate registration_end_time is before event start_time
        if reg_end and start and reg_end >= start:
            self.add_error('registration_end_time', 'Registration end time must be before event start time.')

        # Validate registration_limit is positive if set
        if limit is not None and limit <= 0:
            self.add_error('registration_limit', 'Registration limit must be a positive number.')
