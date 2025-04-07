from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import ValidationError
from .constants import CATEGORIES, DEFAULT_CATEGORIES, DEFAULT_CATEGORY_ICONS

class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, help_text="Optional description of the category")
    icon = models.CharField(max_length=50, default='receipt')  # FontAwesome icon name
    color = models.CharField(max_length=50, default='primary')  # Bootstrap color name
    budget = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Monthly budget amount
    is_active = models.BooleanField(default=True, help_text="Whether this category is currently active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'
        unique_together = ['user', 'name']
        ordering = ['name']

    def __str__(self):
        return self.name

    @classmethod
    def create_default_categories(cls, user):
        """Create default categories for a new user"""
        for category_name, color in DEFAULT_CATEGORIES.items():
            if not cls.objects.filter(user=user, name=category_name).exists():
                cls.objects.create(
                    user=user,
                    name=category_name,
                    color=color,
                    icon=DEFAULT_CATEGORY_ICONS.get(category_name, 'receipt'),
                    description=f"Default {category_name} category"
                )

    @property
    def total_spent(self):
        """Calculate total spent in this category for the current month"""
        current_month = timezone.now().date().replace(day=1)
        return self.expense_set.filter(
            date__gte=current_month,
            date__lt=current_month.replace(day=28) + timezone.timedelta(days=4)
        ).aggregate(total=models.Sum('amount'))['total'] or 0

    @property
    def remaining_budget(self):
        """Calculate remaining budget for the current month"""
        return self.budget - self.total_spent

    @property
    def budget_percentage(self):
        """Calculate percentage of budget used"""
        if self.budget > 0:
            return (self.total_spent / self.budget) * 100
        return 0

    def get_statistics(self, start_date=None, end_date=None):
        """Get category statistics for a given date range"""
        if not start_date:
            start_date = timezone.now().date().replace(day=1)
        if not end_date:
            end_date = timezone.now().date()

        expenses = self.expense_set.filter(date__range=[start_date, end_date])
        total_spent = expenses.aggregate(total=models.Sum('amount'))['total'] or 0
        expense_count = expenses.count()
        avg_expense = total_spent / expense_count if expense_count > 0 else 0

        return {
            'total_spent': total_spent,
            'expense_count': expense_count,
            'average_expense': avg_expense,
            'budget_used': (total_spent / self.budget * 100) if self.budget > 0 else 0
        }

class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='budget_entries')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ['user', 'category']

    def __str__(self):
        return f"{self.category.name} - ${self.amount}"

class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=200)
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.description} - ${self.amount}"

    def clean(self):
        current_date = timezone.now().date()
        if self.date and self.date > current_date:
            raise ValidationError({'date': 'Expense date cannot be in the future.'})

    class Meta:
        ordering = ['-date', '-created_at']

class IncomeSource(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default='money-bill-wave')  # FontAwesome icon name
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Income(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    source = models.ForeignKey(IncomeSource, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.source.name} - ₹{self.amount}"

    def clean(self):
        current_date = timezone.now().date()
        if self.date and self.date > current_date:
            raise ValidationError({'date': 'Income date cannot be in the future.'})

    class Meta:
        ordering = ['-date']

class MonthlyBudget(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    income = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    savings_target = models.DecimalField(max_digits=5, decimal_places=2, default=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Monthly Budget"

    @property
    def target_expenses(self):
        """Calculate target expenses based on income and savings target"""
        if self.income > 0:
            return self.income * (1 - self.savings_target / 100)
        return 0
