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
    # Get current month's start and end dates
    today = timezone.now()
    month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if today.month == 12:
        month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

    # Get expenses for the current month
    expenses = Expense.objects.filter(
        user=request.user,
        date__range=[month_start, month_end]
    )

    # Calculate totals
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0
    total_income = request.user.income_set.filter(
        date__range=[month_start, month_end]
    ).aggregate(total=Sum('amount'))['total'] or 0
    total_balance = total_income - total_expenses
    total_savings = total_income * 0.2  # Assuming 20% savings goal

    # Get recent expenses
    recent_expenses = Expense.objects.filter(
        user=request.user
    ).select_related('category').order_by('-date')[:5]

    # Get budget categories with progress
    budget_categories = []
    categories = Category.objects.filter(user=request.user)
    
    for category in categories:
        budget = Budget.objects.filter(user=request.user, category=category).first()
        if budget:
            spent = expenses.filter(category=category).aggregate(total=Sum('amount'))['total'] or 0
            percentage = (spent / budget.amount * 100) if budget.amount > 0 else 0
            budget_categories.append({
                'name': category.name,
                'icon': category.icon,
                'color': category.color,
                'spent': spent,
                'budget': budget.amount,
                'percentage': min(percentage, 100)  # Cap at 100%
            })

    context = {
        'total_balance': total_balance,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'total_savings': total_savings,
        'recent_expenses': recent_expenses,
        'budget_categories': budget_categories,
    }

    return render(request, 'dashboard.html', context)

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
        category = get_object_or_404(Category, id=request.POST.get('category'), user=request.user)
        Transaction.objects.create(
            user=request.user,
            type=request.POST.get('type'),
            amount=Decimal(request.POST.get('amount', 0)),
            category=category,
            description=request.POST.get('description'),
            date=request.POST.get('date')
        )
        messages.success(request, 'Transaction added successfully.')
    return redirect('dashboard')

@login_required
def income_list(request):
    incomes = Income.objects.filter(user=request.user).order_by('-date')
    income_sources = IncomeSource.objects.all()
    
    context = {
        'incomes': incomes,
        'income_sources': income_sources,
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
            source = IncomeSource.objects.get(id=source_id)
            Income.objects.create(
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
