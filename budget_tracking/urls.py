"""
URL configuration for budget_tracking project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from dj_rest_auth.registration.views import VerifyEmailView, ResendEmailVerificationView
from dj_rest_auth.views import LoginView, LogoutView, PasswordResetView, PasswordResetConfirmView
from budget.views import register, custom_logout, custom_password_reset

urlpatterns = [
     path('', include('budget.urls')),
    path('admin/', admin.site.urls),
    
    # Web Authentication
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', custom_logout, name='logout'),
    path('accounts/register/', register, name='register'),
    path('accounts/password-reset/', custom_password_reset, name='password_reset'),
    path('accounts/password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('accounts/password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('accounts/password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
    
    # JWT Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # REST Authentication
    path('api/auth/login/', LoginView.as_view(), name='rest_login'),
    path('api/auth/logout/', LogoutView.as_view(), name='rest_logout'),
    path('api/auth/register/', register, name='rest_register'),
    path('api/auth/verify-email/', VerifyEmailView.as_view(), name='rest_verify_email'),
    path('api/auth/resend-email/', ResendEmailVerificationView.as_view(), name='rest_resend_email'),
    path('api/auth/password/reset/', PasswordResetView.as_view(), name='rest_password_reset'),
    path('api/auth/password/reset/confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='rest_password_reset_confirm'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
