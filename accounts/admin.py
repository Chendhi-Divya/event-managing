from django.contrib import admin
from .models import Event

# Register your models here.
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'password', 'is_staff', 'is_active')  # Add 'password' here

# Unregister the original User admin
admin.site.unregister(User)

# Register User with your custom UserAdmin
admin.site.register(User, UserAdmin)

class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_owners', 'event_date', 'created_at','get_registrants')
    search_fields = ('title', 'owners__username')
    list_filter = ('event_date', 'owners')

    def get_owners(self, obj):
        return ", ".join([user.username for user in obj.owners.all()])
    get_owners.short_description = 'Owners'

    def get_registrants(self, obj):
        return ", ".join([user.email for user in obj.registrants.all()])
    get_registrants.short_description = 'Registrants Emails'

admin.site.register(Event, EventAdmin)
