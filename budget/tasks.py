# This file is intentionally left empty

from celery import shared_task
from django.utils import timezone
from django.db.models import Sum
from .models import MonthlyBudget, Expense, Category, Budget, User
from django.core.cache import cache
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings

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

@shared_task
def send_budget_alerts():
    """
    Send daily budget alerts to users who are close to or have exceeded their budget limits.
    """
    today = timezone.now().date()
    users = User.objects.filter(is_active=True)
    
    for user in users:
        # Get user's budget categories
        categories = Budget.objects.filter(user=user)
        
        for category in categories:
            # Calculate spent amount for the current month
            spent = Expense.objects.filter(
                user=user,
                category=category.category,
                date__year=today.year,
                date__month=today.month
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            # Calculate percentage used
            percentage = (spent / category.amount * 100) if category.amount > 0 else 0
            
            # Send alert if budget is close to or exceeded
            if percentage >= 80:
                subject = f'Budget Alert: {category.category.name}'
                message = f"""
                Hello {user.first_name},
                
                Your budget for {category.category.name} is at {percentage:.1f}% of the limit.
                Spent: ₹{spent:.2f}
                Budget: ₹{category.amount:.2f}
                
                Please review your expenses to stay within budget.
                
                Best regards,
                Budget Tracker
                """
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )

@shared_task
def generate_monthly_reports():
    """
    Generate and send monthly financial reports to users.
    """
    today = timezone.now().date()
    last_month = today.replace(day=1) - timedelta(days=1)
    
    users = User.objects.filter(is_active=True)
    
    for user in users:
        # Calculate monthly totals
        expenses = Expense.objects.filter(
            user=user,
            date__year=last_month.year,
            date__month=last_month.month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        income = Income.objects.filter(
            user=user,
            date__year=last_month.year,
            date__month=last_month.month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        savings = income - expenses
        
        subject = f'Monthly Financial Report - {last_month.strftime("%B %Y")}'
        message = f"""
        Hello {user.first_name},
        
        Here's your financial summary for {last_month.strftime("%B %Y")}:
        
        Total Income: ₹{income:.2f}
        Total Expenses: ₹{expenses:.2f}
        Net Savings: ₹{savings:.2f}
        
        Please find the detailed report attached.
        
        Best regards,
        Budget Tracker
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

@shared_task
def cleanup_old_data():
    """
    Clean up old data to maintain database performance.
    """
    # Keep data for 5 years
    cutoff_date = timezone.now().date() - timedelta(days=5*365)
    
    # Archive and delete old expenses
    Expense.objects.filter(date__lt=cutoff_date).delete()
    
    # Archive and delete old income records
    Income.objects.filter(date__lt=cutoff_date).delete()
    
    # Clean up old budget records
    Budget.objects.filter(created_at__lt=cutoff_date).delete()
