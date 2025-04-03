from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Expense, Category, MonthlyBudget, Budget, Income, IncomeSource, CATEGORIES
from .serializers import ExpenseSerializer
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
import json
from datetime import datetime, timedelta
from django.utils import timezone
from decimal import Decimal
from .forms import CustomUserCreationForm, ExpenseForm
from django.contrib.auth import logout
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]
    queryset = Expense.objects.all()

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')

def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

@login_required
def expense_list(request):
    expenses = Expense.objects.filter(user=request.user).order_by('-date')
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'expenses': expenses,
        'total_expenses': total_expenses,
    }
    return render(request, 'expense_list.html', context)

@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST, user=request.user)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            messages.success(request, 'Expense added successfully!')
            return redirect('expense_list')
    else:
        form = ExpenseForm(user=request.user)
    return render(request, 'expense_form.html', {'form': form})

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
    return render(request, 'expense_form.html', {'form': form, 'expense': expense})

@login_required
def delete_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense deleted successfully!')
        return redirect('expense_list')
    return render(request, 'expense_confirm_delete.html', {'expense': expense})

@login_required
def dashboard(request):
    # Get total balance
    total_income = Income.objects.filter(user=request.user).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_expenses = Expense.objects.filter(user=request.user).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_balance = total_income - total_expenses
    total_savings = total_balance  # You might want to calculate this differently

    context = {
        'total_balance': total_balance,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'total_savings': total_savings,
    }
    return render(request, 'dashboard.html', context)

@login_required
def income_list(request):
    # Get all income sources
    sources = IncomeSource.objects.filter(user=request.user)
    
    # Get all income records
    incomes = Income.objects.filter(user=request.user).order_by('-date')
    
    context = {
        'sources': sources,
        'incomes': incomes,
    }
    return render(request, 'income_list.html', context)

@login_required
def add_income(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        date = request.POST.get('date')
        
        try:
            # Assuming you want to use the first income source as default
            source = IncomeSource.objects.filter(user=request.user).first()
            if source:
                income = Income.objects.create(
                    user=request.user,
                    source=source,
                    amount=amount,
                    description=description,
                    date=date
                )
                messages.success(request, 'Income added successfully!')
            else:
                messages.error(request, 'No income sources available.')
        except Exception as e:
            messages.error(request, f'Error adding income: {str(e)}')
        
        return redirect('income_list')
    
    return redirect('income_list')

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
    
    # Refresh categories after creating any missing ones
    categories = Category.objects.filter(user=request.user)
    monthly_budget = MonthlyBudget.objects.filter(user=request.user).first()
    
    # Calculate spent amount for each category
    for category in categories:
        spent = Expense.objects.filter(
            user=request.user,
            category=category,
            date__month=timezone.now().month
        ).aggregate(total=Sum('amount'))['total'] or 0
        category.spent = spent
        category.remaining = category.budget - spent if category.budget else 0
    
    context = {
        'categories': categories,
        'monthly_budget': monthly_budget,
    }
    return render(request, 'budget_settings.html', context)

@login_required
def update_monthly_budget(request):
    if request.method == 'POST':
        monthly_budget, created = MonthlyBudget.objects.get_or_create(user=request.user)
        monthly_budget.income = Decimal(request.POST.get('monthly_income', 0))
        monthly_budget.savings_target = Decimal(request.POST.get('savings_target', 20))
        monthly_budget.save()
        messages.success(request, 'Monthly budget updated successfully.')
    return redirect('budget_settings')

@login_required
def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        # Validate that the name is in the CATEGORIES list
        if not any(name == category[0] for category in CATEGORIES):
            messages.error(request, 'Invalid category selected.')
            return redirect('budget_settings')
            
        try:
            Category.objects.create(
                user=request.user,
                name=name,
                budget=Decimal(request.POST.get('budget', 0)),
                icon=request.POST.get('icon', 'ellipsis-h')
            )
            messages.success(request, 'Category added successfully.')
        except Exception as e:
            messages.error(request, f'Error adding category: {str(e)}')
    return redirect('budget_settings')

@login_required
def update_category(request, category_id):
    if request.method == 'POST':
        name = request.POST.get('name')
        # Validate that the name is in the CATEGORIES list
        if not any(name == category[0] for category in CATEGORIES):
            messages.error(request, 'Invalid category selected.')
            return redirect('budget_settings')
            
        try:
            category = get_object_or_404(Category, id=category_id, user=request.user)
            category.name = name
            category.budget = Decimal(request.POST.get('budget', 0))
            category.icon = request.POST.get('icon', 'ellipsis-h')
            category.save()
            messages.success(request, 'Category updated successfully.')
        except Exception as e:
            messages.error(request, f'Error updating category: {str(e)}')
    return redirect('budget_settings')

@login_required
def delete_category(request, category_id):
    if request.method == 'POST':
        category = get_object_or_404(Category, id=category_id, user=request.user)
        category.delete()
        messages.success(request, 'Category deleted successfully.')
    return redirect('budget_settings')

@login_required
def add_transaction(request):
    if request.method == 'POST':
        category_id = request.POST.get('category')
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        date = request.POST.get('date')
        
        try:
            category = Category.objects.get(id=category_id, user=request.user)
            expense = Expense.objects.create(
                user=request.user,
                category=category,
                amount=amount,
                description=description,
                date=date
            )
            messages.success(request, 'Transaction added successfully!')
        except Exception as e:
            messages.error(request, f'Error adding transaction: {str(e)}')
        
        return redirect('dashboard')
    
    return redirect('dashboard')

@login_required
def income_source_list(request):
    sources = IncomeSource.objects.filter(user=request.user)
    return render(request, 'income_source_list.html', {'sources': sources})

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
    return render(request, 'edit_income_source.html', {'source': source})

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
    
    return render(request, 'reports.html', context)

def custom_logout(request):
    logout(request)
    return redirect('home')

@login_required
@require_http_methods(["GET"])
def get_transaction(request, transaction_id):
    transaction = get_object_or_404(Expense, id=transaction_id, user=request.user)
    data = {
        'id': transaction.id,
        'category': transaction.category.id,
        'amount': str(transaction.amount),
        'description': transaction.description,
        'date': transaction.date.strftime('%Y-%m-%d')
    }
    return JsonResponse(data)

@login_required
@require_http_methods(["POST"])
def edit_transaction(request, transaction_id):
    transaction = get_object_or_404(Expense, id=transaction_id, user=request.user)
    
    # Update transaction fields
    transaction.category_id = request.POST.get('category')
    transaction.amount = request.POST.get('amount')
    transaction.description = request.POST.get('description')
    transaction.date = request.POST.get('date')
    transaction.save()
    
    messages.success(request, 'Transaction updated successfully!')
    return redirect('dashboard')

@login_required
@require_http_methods(["POST"])
def delete_transaction(request, transaction_id):
    transaction = get_object_or_404(Expense, id=transaction_id, user=request.user)
    transaction.delete()
    messages.success(request, 'Transaction deleted successfully!')
    return redirect('dashboard')
