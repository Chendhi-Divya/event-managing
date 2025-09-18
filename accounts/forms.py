from django import forms
from .models import Event

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'event_date', 'meeting_link', 'start_time', 'end_time', 'registration_limit', 'registration_end_time']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'event_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'meeting_link': forms.URLInput(attrs={'class': 'form-control'}),
            'start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'registration_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'registration_end_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
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
