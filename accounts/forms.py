# from django import forms
# from .models import Event
# from django.contrib.auth.models import User

# class EventForm(forms.ModelForm):
#      invitation_emails = forms.CharField(
#         required=False,
#         widget=forms.Textarea(attrs={"placeholder": "Enter comma-separated emails"}),
#         help_text="Enter email addresses separated by commas."
#     )
#      class Meta:
#         model = Event
#         fields = [
#             'title', 'description', 'event_date', 'start_time', 'end_time',
#             'max_participants', 'meeting_link', 'registration_deadline',
#         ]
#         widgets = {
#             'title': forms.TextInput(attrs={'class': 'form-control'}),
#             'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
#             'event_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
#             'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
#             'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
#             'max_participants': forms.NumberInput(attrs={'class': 'form-control'}),
#             'meeting_link': forms.URLInput(attrs={'class': 'form-control'}),
#             'registration_deadline': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
#         }
from django import forms
from .models import Event

class EventForm(forms.ModelForm):
    invitation_emails = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"placeholder": "Enter comma-separated emails", "class": "form-control", "rows": "2"}),
        help_text="Enter email addresses separated by commas."
    )

    class Meta:
        model = Event
        fields = [
            'title', 'description', 'event_date', 'start_time', 'end_time',
            'max_participants', 'meeting_link', 'registration_deadline',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'event_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'max_participants': forms.NumberInput(attrs={'class': 'form-control'}),
            'meeting_link': forms.URLInput(attrs={'class': 'form-control'}),
            'registration_deadline': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
