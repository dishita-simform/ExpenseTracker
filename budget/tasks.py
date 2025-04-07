# This file is intentionally left empty

from celery import shared_task
from django.utils import timezone
from django.db.models import Sum
from .models import MonthlyBudget, Expense, Category
from django.core.cache import cache
from datetime import timedelta

@shared_task
def reset_monthly_budgets():
    """Reset monthly budgets at the start of each month"""
    today = timezone.now().date()
    if today.day == 1:  # First day of the month
        MonthlyBudget.objects.all().update(
            target_expenses=0,
            actual_expenses=0
        )
        return "Monthly budgets reset successfully"
    return "Not first day of month, skipping reset"

@shared_task
def generate_daily_expense_summary():
    """Generate daily expense summary and cache it"""
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    # Calculate total expenses for yesterday
    total_expenses = Expense.objects.filter(
        date=yesterday
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Calculate expenses by category
    category_expenses = Expense.objects.filter(
        date=yesterday
    ).values('category__name').annotate(
        total=Sum('amount')
    )
    
    # Cache the results
    cache_key = f"expense_summary:{yesterday}"
    cache.set(cache_key, {
        'total': total_expenses,
        'by_category': list(category_expenses)
    }, timeout=86400)  # Cache for 24 hours
    
    return f"Daily expense summary generated for {yesterday}"

@shared_task
def cleanup_old_expenses():
    """Archive expenses older than 1 year"""
    one_year_ago = timezone.now().date() - timedelta(days=365)
    old_expenses = Expense.objects.filter(date__lt=one_year_ago)
    
    # Archive the expenses (you can implement your archiving logic here)
    archived_count = old_expenses.count()
    old_expenses.delete()
    
    return f"Archived {archived_count} old expenses"
