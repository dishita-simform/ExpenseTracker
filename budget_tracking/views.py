from django.contrib.auth import views as auth_views
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages

class CustomLogoutView(auth_views.LogoutView):
    def dispatch(self, request, *args, **kwargs):
        # Delete all sessions for the current user
        if request.user.is_authenticated:
            request.user.auth_token_set.all().delete()  # Delete auth tokens if using token authentication
            request.session.flush()  # Clear the session
        return super().dispatch(request, *args, **kwargs)

    def get_next_page(self):
        return 'login' 