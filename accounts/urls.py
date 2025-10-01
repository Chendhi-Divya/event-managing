from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),                   # Home page
    path('signup/', views.signup, name='signup'),        # Signup page
    path('login/', views.login_view, name='login'),      # Login page
    path('verify-otp/', views.verify_otp, name='verify_otp'),  # OTP verification
    path('logout/', views.logout_view, name='logout'),   # Logout
    path('dashboard/', views.dashboard, name='dashboard'),
     path('my-events/', views.my_events, name='my_events'),
     path('add-event/', views.add_event, name='add_event'),
     path('registered-events/', views.registered_events, name='registered_events'),
     path('unregister-event/<int:event_id>/', views.unregister_event, name='unregister_event'),
     path('api/token-login/', views.api_token_login, name="api_token_login"),


    # Event management URLs
    path('events/', views.event_list, name='event_list'),        # List of events
    path('events/<int:event_id>/', views.event_detail, name='event_detail'),  # Event detail
    path('events/<int:event_id>/register/', views.register_event, name='register_event'),  # Register for event
     path('register/<int:event_id>/', views.register_event, name='register_event'),
     path('events/add/', views.add_event, name='add_event'),
     path('events/<int:event_id>/registered/', views.registration_success, name='registration_success'),
     path('events/<int:event_id>/', views.event_detail, name='event_detail'),
      path('edit-event/<int:event_id>/', views.edit_event, name='edit_event'),
    path('delete-event/<int:event_id>/', views.delete_event, name='delete_event'),
     

    # Password reset URLs
    path("password-reset/",
         auth_views.PasswordResetView.as_view(template_name="accounts/password_reset.html"),
         name="password_reset"),
    path("password-reset/done/",
         auth_views.PasswordResetDoneView.as_view(template_name="accounts/password_reset_done.html"),
         name="password_reset_done"),
    path("reset/<uidb64>/<token>/",
         auth_views.PasswordResetConfirmView.as_view(template_name="accounts/password_reset_confirm.html"),
         name="password_reset_confirm"),
    path("reset/done/",
         auth_views.PasswordResetCompleteView.as_view(template_name="accounts/password_reset_complete.html"),
         name="password_reset_complete"),
]
