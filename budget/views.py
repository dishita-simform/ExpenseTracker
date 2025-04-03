from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Expense, Category, MonthlyBudget, Budget, Income, IncomeSource
from .serializers import ExpenseSerializer
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
import json
from datetime import datetime, timedelta
from django.utils import timezone
from decimal import Decimal
from .forms import CustomUserCreationForm

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
    return render(request, 'expense_list.html', {'expenses': expenses})

@login_required
def dashboard(request):
    # Get total balance
    total_income = Income.objects.filter(user=request.user).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_expenses = Expense.objects.filter(user=request.user).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_balance = total_income - total_expenses
    total_savings = total_balance  # You might want to calculate this differently

    # Get recent expenses
    recent_expenses = Expense.objects.filter(user=request.user).order_by('-date')[:5]

    # Get budget categories with spent amounts
    categories = Category.objects.filter(user=request.user)
    budget_categories = []
    for category in categories:
        spent = Expense.objects.filter(user=request.user, category=category).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        budget = category.budget or Decimal('0.00')
        percentage = (spent / budget * 100) if budget > 0 else 0
        budget_categories.append({
            'name': category.name,
            'color': category.color,
            'icon': category.icon,
            'spent': spent,
            'budget': budget,
            'percentage': percentage
        })

    context = {
        'total_balance': total_balance,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'total_savings': total_savings,
        'recent_expenses': recent_expenses,
        'budget_categories': budget_categories,
        'categories': categories,
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
        source_id = request.POST.get('source')
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        date = request.POST.get('date')
        
        try:
            source = IncomeSource.objects.get(id=source_id, user=request.user)
            income = Income.objects.create(
                user=request.user,
                source=source,
                amount=amount,
                description=description,
                date=date
            )
            messages.success(request, 'Income added successfully!')
        except Exception as e:
            messages.error(request, f'Error adding income: {str(e)}')
        
        return redirect('income_list')
    
    return redirect('income_list')

@login_required
def budget_settings(request):
    return render(request, 'budget_settings.html')

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
        Category.objects.create(
            user=request.user,
            name=request.POST.get('name'),
            budget=Decimal(request.POST.get('budget', 0)),
            icon=request.POST.get('icon', 'ellipsis-h')
        )
        messages.success(request, 'Category added successfully.')
    return redirect('budget_settings')

@login_required
def update_category(request, category_id):
    if request.method == 'POST':
        category = get_object_or_404(Category, id=category_id, user=request.user)
        category.name = request.POST.get('name')
        category.budget = Decimal(request.POST.get('budget', 0))
        category.icon = request.POST.get('icon', 'ellipsis-h')
        category.save()
        messages.success(request, 'Category updated successfully.')
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
