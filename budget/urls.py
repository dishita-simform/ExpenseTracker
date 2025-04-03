from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.shortcuts import redirect
from . import views

router = DefaultRouter()
router.register(r'expenses', views.ExpenseViewSet, basename='expense')

def home(request):
    return redirect('dashboard')

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('home/', home, name='home'),
    path('register/', views.register, name='register'),
    path('expenses/', views.expense_list, name='expense_list'),
    path('income/', views.income_list, name='income_list'),
    path('add-income/', views.add_income, name='add_income'),
    path('income-sources/', views.income_source_list, name='income_source_list'),
    path('income-sources/add/', views.add_income_source, name='add_income_source'),
    path('income-sources/<int:source_id>/edit/', views.edit_income_source, name='edit_income_source'),
    path('income-sources/<int:source_id>/delete/', views.delete_income_source, name='delete_income_source'),
    path('add-transaction/', views.add_transaction, name='add_transaction'),
    path('budget-settings/', views.budget_settings, name='budget_settings'),
    path('budget-settings/update-monthly/', views.update_monthly_budget, name='update_monthly_budget'),
    path('budget-settings/add-category/', views.add_category, name='add_category'),
    path('budget-settings/update-category/<int:category_id>/', views.update_category, name='update_category'),
    path('budget-settings/delete-category/<int:category_id>/', views.delete_category, name='delete_category'),
    path('api/', include(router.urls)),
]
