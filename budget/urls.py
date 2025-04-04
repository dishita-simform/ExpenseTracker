from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.shortcuts import redirect
from . import views

router = DefaultRouter()
router.register(r'api/expenses', views.ExpenseViewSet, basename='expense')

def home(request):
    return redirect('dashboard')

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('home/', home, name='home'),
    path('register/', views.register, name='register'),
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/add/', views.add_expense, name='add_expense'),
    path('expenses/<int:expense_id>/edit/', views.edit_expense, name='edit_expense'),
    path('expenses/<int:expense_id>/delete/', views.delete_expense, name='delete_expense'),
    path('income/', views.income_list, name='income_list'),
    path('add-income/', views.add_income, name='add_income'),
    path('income-sources/', views.income_source_list, name='income_source_list'),
    path('income-sources/add/', views.add_income_source, name='add_income_source'),
    path('income-sources/<int:source_id>/edit/', views.edit_income_source, name='edit_income_source'),
    path('income-sources/<int:source_id>/delete/', views.delete_income_source, name='delete_income_source'),
    path('add-transaction/', views.add_transaction, name='add_transaction'),
    path('budget-settings/', views.budget_settings, name='budget_settings'),
    path('budget-settings/update-monthly/', views.update_monthly_budget, name='update_monthly_budget'),
    path('reports/', views.reports, name='reports'),
    path('api/', include(router.urls)),
    path('api/transaction/<int:transaction_id>/', views.get_transaction, name='get_transaction'),
    path('transaction/<int:transaction_id>/edit/', views.edit_transaction, name='edit_transaction'),
    path('transaction/<int:transaction_id>/delete/', views.delete_transaction, name='delete_transaction'),
    path('budget-history/', views.budget_history, name='budget_history'),
    path('api/dashboard-data/', views.dashboard_data, name='dashboard_data'),
]
