from django.contrib import admin
from .models import Event

# Register your models here.
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'password', 'is_staff', 'is_active')  # Add 'password' here

# Unregister the original User admin
admin.site.unregister(User)

# Register User with your custom UserAdmin
admin.site.register(User, UserAdmin)

class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'event_date', 'created_at')
    search_fields = ('title', 'user__username')
    list_filter = ('event_date', 'user')

admin.site.register(Event, EventAdmin)
