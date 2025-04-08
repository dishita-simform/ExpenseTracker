from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Expense, Category, MonthlyBudget, Budget, Income, IncomeSource, CATEGORIES
from .serializers import ExpenseSerializer, CategorySerializer
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, F, Count, Avg
from django.db.models.functions import TruncMonth, ExtractMonth, ExtractYear
import json
from datetime import datetime, timedelta, date
from django.utils import timezone
from decimal import Decimal
from .forms import CustomUserCreationForm, ExpenseForm, IncomeForm, BudgetForm
from django.contrib.auth import logout
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .constants import CATEGORIES, DEFAULT_CATEGORIES, DEFAULT_CATEGORY_ICONS
import calendar
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db import connection
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy

User = get_user_model()

class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Expense.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'budget/home.html')

def register(request):
    """
    View for user registration.
    Handles both form-based and API-based registration.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in after registration
            from django.contrib.auth import login
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to Budget Tracker.')
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

@login_required
def expense_list(request):
    # Get all available years from expense records
    available_years = sorted(set(exp.date.year for exp in Expense.objects.filter(user=request.user)), reverse=True)
    if not available_years:
        available_years = [timezone.now().year]
    
    # Get selected month and year from request or default to current month
    selected_month = request.GET.get('month', timezone.now().month)
    selected_year = request.GET.get('year', timezone.now().year)
    
    # Convert to integers
    try:
        selected_month = int(selected_month)
        selected_year = int(selected_year)
    except (ValueError, TypeError):
        selected_month = timezone.now().month
        selected_year = timezone.now().year
    
    # Get expenses for selected month
    expenses = Expense.objects.filter(
        user=request.user,
        date__month=selected_month,
        date__year=selected_year
    ).order_by('-date', '-id')
    
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    
    # Create month names for dropdown
    month_names = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]
    
    context = {
        'expenses': expenses,
        'total_expenses': total_expenses,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'available_years': available_years,
        'month_names': month_names,
        'selected_month_name': dict(month_names)[selected_month],
    }
    return render(request, 'budget/expense_list.html', context)

@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            messages.success(request, 'Expense added successfully!')
            return redirect('expense_list')
    else:
        form = ExpenseForm()
        # Get user's categories
        categories = Category.objects.filter(user=request.user)
        form.fields['category'].queryset = categories
    
    return render(request, 'budget/add_expense.html', {'form': form})

@login_required
def edit_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense updated successfully!')
            return redirect('expense_list')
    else:
        form = ExpenseForm(instance=expense, user=request.user)
    
    # Get current date for the template
    today = timezone.now().date()
    return render(request, 'budget/expense_form.html', {'form': form, 'expense': expense, 'today': today})

@login_required
def delete_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense deleted successfully!')
        return redirect('expense_list')
    return render(request, 'budget/expense_confirm_delete.html', {'expense': expense})

@login_required
def dashboard(request):
    # Get total balance
    total_income = Income.objects.filter(user=request.user).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_expenses = Expense.objects.filter(user=request.user).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_balance = total_income - total_expenses
    total_savings = total_balance

    # Get selected month and year from request or default to current month
    selected_month = request.GET.get('month', timezone.now().month)
    selected_year = request.GET.get('year', timezone.now().year)
    
    # Convert to integers
    try:
        selected_month = int(selected_month)
        selected_year = int(selected_year)
    except (ValueError, TypeError):
        selected_month = timezone.now().month
        selected_year = timezone.now().year
    
    # Get all available years
    available_years = sorted(set(exp.date.year for exp in Expense.objects.filter(user=request.user)), reverse=True)
    if not available_years:
        available_years = [timezone.now().year]
    
    # Create month names for dropdown
    month_names = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]

    # Get all transactions and combine them
    expenses = list(Expense.objects.filter(
        user=request.user,
        date__month=selected_month,
        date__year=selected_year
    ).values(
        'id', 'category__name', 'category__icon', 'category__color',
        'description', 'amount', 'date'
    ).order_by('-date', '-id'))
    
    incomes = list(Income.objects.filter(
        user=request.user,
        date__month=selected_month,
        date__year=selected_year
    ).values(
        'id', 'source__name', 'description', 'amount', 'date'
    ).order_by('-date', '-id'))

    # Combine and sort transactions
    recent_transactions = []
    for expense in expenses:
        recent_transactions.append({
            'id': expense['id'],
            'category': {
                'name': expense['category__name'],
                'icon': expense['category__icon'],
                'color': expense['category__color']
            },
            'description': expense['description'],
            'amount': -expense['amount'],  # Negative for expenses
            'date': expense['date'],
            'type': 'expense'
        })

    for income in incomes:
        recent_transactions.append({
            'id': income['id'],
            'category': {
                'name': income['source__name'],
                'icon': 'money-bill-wave',
                'color': 'success'
            },
            'description': income['description'] or income['source__name'],
            'amount': income['amount'],
            'date': income['date'],
            'type': 'income'
        })

    # Sort combined transactions by date and limit to 3
    recent_transactions.sort(key=lambda x: (x['date'], x['id']), reverse=True)
    recent_transactions = recent_transactions[:3]

    # Define color mapping for each category
    category_colors = {
        'Rent': '#4B0082',        # Indigo
        'Food': '#32CD32',        # Lime Green
        'Travel': '#1E90FF',      # Dodger Blue
        'Bills': '#DC143C',       # Crimson
        'Entertainment': '#FF69B4',# Hot Pink
        'Shopping': '#FF4500',    # Orange Red
        'Healthcare': '#FF6347',   # Tomato
        'Education': '#6A5ACD',   # Slate Blue
        'Transportation': '#FFD700',# Gold
        'Utilities': '#00CED1',   # Dark Turquoise
        'Insurance': '#8A2BE2',   # Blue Violet
        'Savings': '#20B2AA',     # Light Sea Green
        'Investment': '#FF8C00',  # Dark Orange
        'Gifts': '#DA70D6',      # Orchid
        'Fitness': '#40E0D0',    # Turquoise
        'Pet': '#FF69B4',        # Hot Pink
        'Home': '#4B0082',       # Indigo
        'Personal Care': '#32CD32',# Lime Green
        'Other': '#6c757d',      # Gray
    }
    
    # Get budget data for pie chart
    categories = Category.objects.filter(user=request.user)
    budget_data = []
    
    for category in categories:
        spent = Expense.objects.filter(
            user=request.user,
            category=category,
            date__month=selected_month,
            date__year=selected_year
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        if spent > 0:  # Only include categories with expenses
            budget_data.append({
                'name': category.name,
                'spent': float(spent),
                'color': category_colors.get(category.name, '#6c757d'),  # Use mapped color or default to gray
                'icon': category.icon
            })

    # Get categories and income sources for the add transaction form
    expense_categories = Category.objects.filter(user=request.user)
    income_sources = IncomeSource.objects.filter(user=request.user)

    # Calculate totals for the selected month
    total_income = Income.objects.filter(
        user=request.user,
        date__month=selected_month,
        date__year=selected_year
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    total_expenses = Expense.objects.filter(
        user=request.user,
        date__month=selected_month,
        date__year=selected_year
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    total_balance = total_income - total_expenses
    total_savings = total_balance if total_balance > 0 else Decimal('0.00')

    context = {
        'total_balance': total_balance,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'total_savings': total_savings,
        'recent_transactions': recent_transactions,
        'budget_data': json.dumps(budget_data),  # Convert to JSON for JavaScript
        'expense_categories': expense_categories,
        'income_sources': income_sources,
        'today': timezone.now().date().isoformat(),  # Add today's date for form validation
        'selected_month': selected_month,
        'selected_year': selected_year,
        'available_years': available_years,
        'month_names': month_names,
        'selected_month_name': dict(month_names)[selected_month]
    }
    return render(request, 'budget/dashboard.html', context)

@login_required
def income_list(request):
    # Get all available years from income records
    available_years = sorted(set(inc.date.year for inc in Income.objects.filter(user=request.user)), reverse=True)
    if not available_years:
        available_years = [timezone.now().year]
    
    # Get selected month and year from request or default to current month
    selected_month = request.GET.get('month', timezone.now().month)
    selected_year = request.GET.get('year', timezone.now().year)
    
    # Convert to integers
    try:
        selected_month = int(selected_month)
        selected_year = int(selected_year)
    except (ValueError, TypeError):
        selected_month = timezone.now().month
        selected_year = timezone.now().year
    
    # Get income records for selected month
    incomes = Income.objects.filter(
        user=request.user,
        date__month=selected_month,
        date__year=selected_year
    ).order_by('-date', '-id')
    
    total_income = incomes.aggregate(total=Sum('amount'))['total'] or 0
    
    # Create month names for dropdown
    month_names = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]
    
    context = {
        'incomes': incomes,
        'total_income': total_income,
        'today': timezone.now().date(),
        'selected_month': selected_month,
        'selected_year': selected_year,
        'available_years': available_years,
        'month_names': month_names,
        'selected_month_name': dict(month_names)[selected_month],
    }
    return render(request, 'budget/income_list.html', context)

@login_required
def add_income(request):
    if request.method == 'POST':
        source_name = request.POST.get('source')
        amount = request.POST.get('amount')
        description = request.POST.get('description', '')
        date_str = request.POST.get('date')
        
        try:
            # Parse the date string to a date object
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Check if the date is in the future
            current_date = timezone.now().date()
            if date > current_date:
                raise ValueError('Income date cannot be in the future.')
            
            # Create or get the income source
            source, created = IncomeSource.objects.get_or_create(
                user=request.user,
                name=source_name,
                defaults={'icon': 'money-bill-wave'}
            )
            
            # Create the income record
            income = Income.objects.create(
                user=request.user,
                source=source,
                amount=amount,
                description=description,
                date=date
            )

            # If this is an AJAX request, return JSON response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Income added successfully',
                    'transaction': {
                        'id': income.id,
                        'type': 'income',
                        'category': {
                            'name': source.name,
                            'icon': 'money-bill-wave',
                            'color': 'success'
                        },
                        'description': description or source.name,
                        'amount': float(amount),
                        'date': date.strftime('%b %d, %Y')
                    }
                })

            messages.success(request, 'Income added successfully!')
            return redirect('dashboard')
            
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
            messages.error(request, f'Error adding income: {str(e)}')
            return redirect('dashboard')
    
    return redirect('dashboard')

@login_required
def budget_settings(request):
    # Get or create categories for the user
    categories = Category.objects.filter(user=request.user)
    existing_category_names = [cat.name for cat in categories]
    
    # Create missing categories from the predefined list
    for category_name, _ in CATEGORIES:
        if category_name not in existing_category_names:
            # Map category names to icons
            icon_map = {
                'Rent': 'home',
                'Food': 'utensils',
                'Travel': 'plane',
                'Bills': 'file-invoice',
                'Entertainment': 'gamepad',
                'Shopping': 'shopping-cart',
                'Healthcare': 'hospital',
                'Education': 'graduation-cap',
                'Transportation': 'car',
                'Utilities': 'bolt',
                'Insurance': 'shield-alt',
                'Savings': 'piggy-bank',
                'Investment': 'chart-line',
                'Gifts': 'gift',
                'Fitness': 'dumbbell',
                'Pet': 'paw',
                'Home': 'home',
                'Personal Care': 'spa',
                'Other': 'ellipsis-h',
            }
            
            Category.objects.create(
                user=request.user,
                name=category_name,
                icon=icon_map.get(category_name, 'ellipsis-h'),
                budget=0
            )
    
    # Get current month and year
    current_date = timezone.now()
    current_month = current_date.month
    current_year = current_date.year
    
    # Refresh categories after creating any missing ones
    categories = Category.objects.filter(user=request.user)
    monthly_budget = MonthlyBudget.objects.filter(user=request.user).first()
    
    # Calculate spent amount for each category for the current month only
    for category in categories:
        spent = Expense.objects.filter(
            user=request.user,
            category=category,
            date__month=current_month,
            date__year=current_year
        ).aggregate(total=Sum('amount'))['total'] or 0
        category.spent = spent
        category.remaining = category.budget - spent if category.budget else 0
    
    # Prepare categories data for JavaScript
    categories_data = []
    for category in categories:
        categories_data.append({
            'id': category.id,
            'name': category.name,
            'budget': float(category.budget) if category.budget else 0,
            'spent': float(category.spent) if category.spent else 0,
            'remaining': float(category.remaining) if category.remaining else 0,
            'icon': category.icon
        })
    
    context = {
        'categories': categories,
        'monthly_budget': monthly_budget,
        'categories_json': json.dumps(categories_data),
        'current_month': current_month,
        'current_year': current_year,
        'month_name': current_date.strftime('%B')
    }
    return render(request, 'budget/budget_settings.html', context)

@login_required
def update_monthly_budget(request):
    if request.method == 'POST':
        # Update monthly budget if provided
        if 'monthly_income' in request.POST or 'savings_target' in request.POST:
            monthly_budget, created = MonthlyBudget.objects.get_or_create(user=request.user)
            monthly_budget.income = Decimal(request.POST.get('monthly_income', 0))
            monthly_budget.savings_target = Decimal(request.POST.get('savings_target', 20))
            monthly_budget.save()
            messages.success(request, 'Monthly budget updated successfully.')
        
        # Update category budget if provided
        if 'category' in request.POST and 'budget_limit' in request.POST:
            category_id = request.POST.get('category')
            budget_limit = Decimal(request.POST.get('budget_limit', 0))
            
            try:
                category = Category.objects.get(id=category_id, user=request.user)
                category.budget = budget_limit
                category.save()
                messages.success(request, f'Budget for {category.name} updated successfully.')
            except Category.DoesNotExist:
                messages.error(request, 'Category not found.')
            except Exception as e:
                messages.error(request, f'Error updating category budget: {str(e)}')
    
    return redirect('budget_settings')

@login_required
def category_list(request):
    categories = Category.objects.filter(user=request.user)
    return render(request, 'budget/category_list.html', {'categories': categories})

@login_required
def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        color = request.POST.get('color')
        icon = request.POST.get('icon')
        description = request.POST.get('description')
        budget = request.POST.get('budget', 0)

        if name:
            category = Category.objects.create(
                user=request.user,
                name=name,
                color=color or DEFAULT_CATEGORIES.get(name, 'primary'),
                icon=icon or DEFAULT_CATEGORY_ICONS.get(name, 'receipt'),
                description=description,
                budget=budget
            )
            messages.success(request, f'Category "{name}" created successfully!')
            return redirect('category_list')
        else:
            messages.error(request, 'Category name is required.')
    
    return render(request, 'budget/add_category.html', {
        'default_colors': DEFAULT_CATEGORIES,
        'default_icons': DEFAULT_CATEGORY_ICONS
    })

@login_required
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id, user=request.user)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        color = request.POST.get('color')
        icon = request.POST.get('icon')
        description = request.POST.get('description')
        budget = request.POST.get('budget')
        is_active = request.POST.get('is_active') == 'on'

        if name:
            category.name = name
            category.color = color
            category.icon = icon
            category.description = description
            category.budget = budget
            category.is_active = is_active
            category.save()
            messages.success(request, f'Category "{name}" updated successfully!')
            return redirect('category_list')
        else:
            messages.error(request, 'Category name is required.')
    
    return render(request, 'budget/edit_category.html', {
        'category': category,
        'default_colors': DEFAULT_CATEGORIES,
        'default_icons': DEFAULT_CATEGORY_ICONS
    })

@login_required
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id, user=request.user)
    
    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.success(request, f'Category "{name}" deleted successfully!')
        return redirect('category_list')
    
    return render(request, 'budget/delete_category.html', {'category': category})

@login_required
def add_transaction(request):
    if request.method == 'POST':
        category_id = request.POST.get('category')
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        date_str = request.POST.get('date')

        try:
            # Parse the date string to a date object
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            category = Category.objects.get(id=category_id, user=request.user)
            
            # Create the expense record
            expense = Expense.objects.create(
                user=request.user,
                category=category,
                amount=amount,
                description=description,
                date=date
            )

            # If this is an AJAX request, return JSON response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Transaction added successfully',
                    'transaction': {
                        'id': expense.id,
                        'type': 'expense',
                        'category': {
                            'name': category.name,
                            'icon': category.icon,
                            'color': category.color
                        },
                        'description': description,
                        'amount': -float(amount),
                        'date': date.strftime('%b %d, %Y')
                    }
                })

            messages.success(request, 'Transaction added successfully!')
            return redirect('dashboard')
            
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
            messages.error(request, f'Error adding transaction: {str(e)}')
            return redirect('dashboard')

    return redirect('dashboard')

@login_required
def income_source_list(request):
    sources = IncomeSource.objects.filter(user=request.user)
    return render(request, 'budget/income_source_list.html', {'sources': sources})

@login_required
def add_income_source(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        icon = request.POST.get('icon')
        IncomeSource.objects.create(user=request.user, name=name, icon=icon)
        messages.success(request, 'Income source added successfully!')
        return redirect('income_source_list')
    return redirect('income_source_list')

@login_required
def edit_income_source(request, source_id):
    source = get_object_or_404(IncomeSource, id=source_id, user=request.user)
    if request.method == 'POST':
        source.name = request.POST.get('name')
        source.icon = request.POST.get('icon')
        source.save()
        messages.success(request, 'Income source updated successfully!')
        return redirect('income_source_list')
    return render(request, 'budget/edit_income_source.html', {'source': source})

@login_required
def delete_income_source(request, source_id):
    source = get_object_or_404(IncomeSource, id=source_id, user=request.user)
    source.delete()
    messages.success(request, 'Income source deleted successfully!')
    return redirect('income_source_list')

@login_required
def reports(request):
    # Get date range from request or default to current month
    today = timezone.now().date()
    start_date = request.GET.get('start_date', today.replace(day=1).isoformat())
    end_date = request.GET.get('end_date', today.isoformat())
    
    # Convert string dates to date objects
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        start_date = today.replace(day=1)
        end_date = today
    
    # Get expenses for the date range
    expenses = Expense.objects.filter(
        user=request.user,
        date__gte=start_date,
        date__lte=end_date
    ).order_by('date')
    
    # Get income for the date range
    income = Income.objects.filter(
        user=request.user,
        date__gte=start_date,
        date__lte=end_date
    ).order_by('date')
    
    # Calculate totals
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    total_income = income.aggregate(total=Sum('amount'))['total'] or 0
    net_income = total_income - total_expenses
    
    # Group expenses by category
    expenses_by_category = {}
    for expense in expenses:
        category_name = expense.category
        if category_name not in expenses_by_category:
            expenses_by_category[category_name] = 0
        expenses_by_category[category_name] += expense.amount
    
    # Group income by source
    income_by_source = {}
    for inc in income:
        source_name = inc.source.name
        if source_name not in income_by_source:
            income_by_source[source_name] = 0
        income_by_source[source_name] += inc.amount
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'expenses': expenses,
        'income': income,
        'total_expenses': total_expenses,
        'total_income': total_income,
        'net_income': net_income,
        'expenses_by_category': expenses_by_category,
        'income_by_source': income_by_source,
    }
    
    return render(request, 'budget/reports.html', context)

def custom_logout(request):
    logout(request)
    return redirect('home')

@login_required
@require_http_methods(["GET"])
def get_transaction(request, transaction_id):
    """API endpoint to get transaction details"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    try:
        expense = Expense.objects.get(id=transaction_id, user=request.user)
        return JsonResponse({
            'id': expense.id,
            'category': expense.category.id,
            'amount': expense.amount,
            'description': expense.description,
            'date': expense.date.strftime('%Y-%m-%d')
        })
    except Expense.DoesNotExist:
        return JsonResponse({'error': 'Transaction not found'}, status=404)

@login_required
@require_http_methods(["POST"])
def edit_transaction(request, transaction_id):
    expense = get_object_or_404(Expense, id=transaction_id, user=request.user)
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Transaction updated successfully'
                })
            
            messages.success(request, 'Transaction updated successfully')
            return redirect('dashboard')
    else:
        form = ExpenseForm(instance=expense)
    
    # If this is an AJAX request but not POST, return error
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': False,
            'error': 'Invalid request method'
        }, status=400)
    
    return render(request, 'budget/expense_form.html', {'form': form, 'expense': expense})

@login_required
@require_http_methods(["POST"])
def delete_transaction(request, transaction_id):
    expense = get_object_or_404(Expense, id=transaction_id, user=request.user)
    
    if request.method == 'POST':
        expense.delete()
        
        # Check if this is an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Transaction deleted successfully'
            })
        
        messages.success(request, 'Transaction deleted successfully')
        return redirect('dashboard')
    
    # If this is an AJAX request but not POST, return error
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': False,
            'error': 'Invalid request method'
        }, status=400)
    
    return render(request, 'budget/confirm_delete.html', {'expense': expense})

@login_required
def budget_history(request):
    # Get all available months and years from expenses
    available_months = Expense.objects.filter(user=request.user).dates('date', 'month').order_by('-date')
    
    # Get selected month and year from request or default to current month
    selected_month = request.GET.get('month', timezone.now().month)
    selected_year = request.GET.get('year', timezone.now().year)
    
    # Convert to integers
    try:
        selected_month = int(selected_month)
        selected_year = int(selected_year)
    except (ValueError, TypeError):
        selected_month = timezone.now().month
        selected_year = timezone.now().year
    
    # Get categories for the user
    categories = Category.objects.filter(user=request.user)
    
    # Calculate spent amount for each category for the selected month
    for category in categories:
        spent = Expense.objects.filter(
            user=request.user,
            category=category,
            date__month=selected_month,
            date__year=selected_year
        ).aggregate(total=Sum('amount'))['total'] or 0
        category.spent = spent
        category.remaining = category.budget - spent if category.budget else 0
    
    # Get all expenses for the selected month
    expenses = Expense.objects.filter(
        user=request.user,
        date__month=selected_month,
        date__year=selected_year
    ).order_by('-date')
    
    # Get all income for the selected month
    income = Income.objects.filter(
        user=request.user,
        date__month=selected_month,
        date__year=selected_year
    ).order_by('-date')
    
    # Calculate total income and expenses
    total_income = income.aggregate(total=Sum('amount'))['total'] or 0
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    
    # Prepare categories data for JavaScript
    categories_data = []
    for category in categories:
        categories_data.append({
            'id': category.id,
            'name': category.name,
            'budget': float(category.budget) if category.budget else 0,
            'spent': float(category.spent) if category.spent else 0,
            'remaining': float(category.remaining) if category.remaining else 0,
            'icon': category.icon
        })
    
    # Get all available years
    available_years = sorted(set(exp.date.year for exp in Expense.objects.filter(user=request.user)), reverse=True)
    
    # Get all available months for the selected year
    available_months_for_year = sorted(set(exp.date.month for exp in Expense.objects.filter(user=request.user, date__year=selected_year)), reverse=True)
    
    # Create month names for dropdown
    month_names = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]
    
    context = {
        'categories': categories,
        'expenses': expenses,
        'income': income,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'categories_json': json.dumps(categories_data),
        'selected_month': selected_month,
        'selected_year': selected_year,
        'available_years': available_years,
        'available_months_for_year': available_months_for_year,
        'month_names': month_names,
        'selected_month_name': dict(month_names)[selected_month],
        'available_months': available_months
    }
    return render(request, 'budget/budget_history.html', context)

@login_required
def dashboard_data(request):
    """API endpoint to get dashboard data for AJAX updates"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    # Get selected month and year from request or default to current month
    selected_month = request.GET.get('month', timezone.now().month)
    selected_year = request.GET.get('year', timezone.now().year)
    
    # Convert to integers
    try:
        selected_month = int(selected_month)
        selected_year = int(selected_year)
    except (ValueError, TypeError):
        selected_month = timezone.now().month
        selected_year = timezone.now().year
    
    # Get month's start and end dates
    month_start = date(selected_year, selected_month, 1)
    if month_start.month == 12:
        next_month = month_start.replace(year=month_start.year + 1, month=1, day=1)
    else:
        next_month = month_start.replace(month=month_start.month + 1, day=1)
    month_end = next_month - timedelta(days=1)
    
    # Get total income for selected month
    total_income = Income.objects.filter(
        user=request.user,
        date__month=selected_month,
        date__year=selected_year
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Get total expenses for selected month
    total_expenses = Expense.objects.filter(
        user=request.user,
        date__month=selected_month,
        date__year=selected_year
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Calculate total balance and savings
    total_balance = total_income - total_expenses
    total_savings = total_balance if total_balance > 0 else 0
    
    # Get transactions for selected month
    expenses = list(Expense.objects.filter(
        user=request.user,
        date__month=selected_month,
        date__year=selected_year
    ).values(
        'id', 'category__name', 'category__icon', 'category__color',
        'description', 'amount', 'date'
    ).order_by('-date', '-id'))
    
    incomes = list(Income.objects.filter(
        user=request.user,
        date__month=selected_month,
        date__year=selected_year
    ).values(
        'id', 'source__name', 'description', 'amount', 'date'
    ).order_by('-date', '-id'))
    
    # Combine and sort transactions
    recent_transactions = []
    for expense in expenses:
        recent_transactions.append({
            'id': expense['id'],
            'type': 'expense',
            'amount': -float(expense['amount']),  # Negative for expenses
            'description': expense['description'],
            'date': expense['date'].strftime('%b %d, %Y'),
            'category': {
                'name': expense['category__name'],
                'color': expense['category__color'],
                'icon': expense['category__icon']
            }
        })
    
    for income in incomes:
        recent_transactions.append({
            'id': income['id'],
            'type': 'income',
            'amount': float(income['amount']),
            'description': income['description'] or income['source__name'],
            'date': income['date'].strftime('%b %d, %Y'),
            'category': {
                'name': income['source__name'],
                'color': 'success',
                'icon': 'money-bill-wave'
            }
        })
    
    # Sort by date (newest first)
    recent_transactions.sort(key=lambda x: datetime.strptime(x['date'], '%b %d, %Y'), reverse=True)
    
    # Get budget categories with spent amounts
    budget_categories = []
    categories = Category.objects.filter(user=request.user)
    
    for category in categories:
        budget = Budget.objects.filter(
            user=request.user,
            category=category,
            month=selected_month,
            year=selected_year
        ).first()
        
        if budget:
            # Calculate spent amount for this category
            spent = Expense.objects.filter(
                user=request.user,
                category=category,
                date__month=selected_month,
                date__year=selected_year
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            # Calculate percentage
            percentage = (spent / budget.amount) * 100 if budget.amount > 0 else 0
            
            budget_categories.append({
                'id': category.id,
                'name': category.name,
                'color': category.color,
                'icon': category.icon,
                'budget': budget.amount,
                'spent': spent,
                'remaining': budget.amount - spent,
                'percentage': min(percentage, 100)  # Cap at 100%
            })
    
    # Return JSON response
    return JsonResponse({
        'total_balance': float(total_balance),
        'total_income': float(total_income),
        'total_expenses': float(total_expenses),
        'total_savings': float(total_savings),
        'recent_transactions': recent_transactions,
        'budget_categories': budget_categories
    })

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = User.objects.get(username=request.data.get('username'))
            response.data['user'] = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        return response

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    API endpoint for user registration.
    Accepts POST requests with username, email, password, first_name, and last_name.
    Returns user data and JWT tokens on success.
    """
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')
    
    # Validate required fields
    if not username or not email or not password:
        return Response({
            'error': 'Please provide username, email and password'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if username already exists
    if User.objects.filter(username=username).exists():
        return Response({
            'error': 'Username already exists'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if email already exists
    if User.objects.filter(email=email).exists():
        return Response({
            'error': 'Email already exists'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate password strength
    if len(password) < 8:
        return Response({
            'error': 'Password must be at least 8 characters long'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Create user
    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({
            'error': f'Registration failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    user = request.user
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def budget_statistics(request):
    """
    Get budget statistics using stored procedure
    """
    month = int(request.GET.get('month', timezone.now().month))
    year = int(request.GET.get('year', timezone.now().year))
    
    with connection.cursor() as cursor:
        cursor.callproc('calculate_monthly_budget', [request.user.id, month, year])
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return Response(results)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def monthly_summary(request):
    """
    Get monthly summary using stored procedure
    """
    month = int(request.GET.get('month', timezone.now().month))
    year = int(request.GET.get('year', timezone.now().year))
    
    with connection.cursor() as cursor:
        cursor.callproc('calculate_monthly_summary', [request.user.id, month, year])
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return Response(results[0] if results else {})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def expense_trends(request):
    """
    Get expense trends using stored procedure
    """
    months = int(request.GET.get('months', 6))
    
    with connection.cursor() as cursor:
        cursor.callproc('get_expense_trends', [request.user.id, months])
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return Response(results)
