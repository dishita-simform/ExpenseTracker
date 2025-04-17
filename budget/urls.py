from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views
from . import views
from rest_framework_simplejwt.views import TokenRefreshView
from .views import budget_statistics, home, monthly_summary, expense_trends

router = DefaultRouter()
router.register(r'expenses', views.ExpenseViewSet, basename='expense')
router.register(r'categories', views.CategoryViewSet, basename='category')

def auth_home(request):
    return redirect('dashboard')

urlpatterns = [
    # Dashboard and home
    path('dashboard/', views.dashboard, name='dashboard'),
    path('auth_home/', auth_home, name='home'),
    path('', home, name='root'),
    
    # Authentication
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', auth_views.PasswordChangeView.as_view(
        template_name='registration/change_password.html',
        success_url='/profile/'
    ), name='change_password'),
    
    # Password Reset
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),

    # Expenses
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/add/', views.add_expense, name='add_expense'),
    path('expenses/<int:expense_id>/edit/', views.edit_expense, name='edit_expense'),
    path('expenses/<int:expense_id>/delete/', views.delete_expense, name='delete_expense'),
    
    # Income
    path('income/', views.income_list, name='income_list'),
    path('income/add/', views.add_income, name='add_income'),
    path('income/<int:income_id>/edit/', views.edit_income, name='edit_income'),
    path('income/<int:income_id>/delete/', views.delete_income, name='delete_income'),
    
    # Budget
    path('budget-settings/', views.budget_settings, name='budget_settings'),
    path('budget-settings/update-monthly/', views.update_monthly_budget, name='update_monthly_budget'),
    path('budget-history/', views.budget_history, name='budget_history'),
    path('manage-category-budgets/', views.manage_category_budgets, name='manage_category_budgets'),
    path('reset-category-budget/<int:category_id>/', views.reset_category_budget, name='reset_category_budget'),
    path('check-budget/<int:category_id>/', views.check_budget, name='check_budget'),
    
    # Reports
    path('reports/', views.reports, name='reports'),
    
    # API endpoints
    path('api/', include(router.urls)),
    path('api/transaction/<int:transaction_id>/', views.get_transaction, name='get_transaction'),
    path('api/dashboard-data/', views.dashboard_data, name='dashboard_data'),
    path('api/category-budget/<int:category_id>/', views.category_budget, name='category_budget'),
   
    # Authentication URLs
    path('api/token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # API Registration Endpoint
    # POST /api/register/
    # Request body: {"username": "string", "email": "string", "password": "string", "first_name": "string" (optional), "last_name": "string" (optional)}
    # Response: {"user": {"id": integer, "username": "string", "email": "string", "first_name": "string", "last_name": "string"}, "refresh": "string", "access": "string", "message": "string"}
    path('api/register/', views.register_user, name='register'),
    path('api/profile/', views.get_user_profile, name='user_profile'),
    
    # Stored Procedure URLs
    path('api/budget-statistics/', budget_statistics, name='budget_statistics'),
    path('api/monthly-summary/', monthly_summary, name='monthly_summary'),
    path('api/expense-trends/', expense_trends, name='expense_trends'),
    path('budget/export-report/', views.export_report, name='export_report'),
    path('test-email/', views.test_email, name='test_email'),
]
