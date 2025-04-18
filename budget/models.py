from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import ValidationError
from .constants import CATEGORIES, DEFAULT_CATEGORIES, DEFAULT_CATEGORY_ICONS
from .validators import (
    validate_positive_amount,
    validate_future_date,
    validate_budget_limit,
    validate_percentage,
    validate_currency_format
)
from django.db.models.signals import post_save
from django.dispatch import receiver

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, default='receipt')  # FontAwesome icon name
    color = models.CharField(max_length=50, default='primary')  # Bootstrap color name

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    @classmethod
    def create_default_categories(cls):
        """Create default categories"""
        for category_name, color in DEFAULT_CATEGORIES.items():
            if not cls.objects.filter(name=category_name).exists():
                cls.objects.create(
                    name=category_name,
                    color=color,
                    icon=DEFAULT_CATEGORY_ICONS.get(category_name, 'receipt')
                )

    @property
    def remaining_budget(self):
        """Calculate the remaining budget for this category."""
        total_budget = self.categorybudget_set.aggregate(total=models.Sum('amount'))['total'] or 0
        total_spent = self.expense_set.aggregate(total=models.Sum('amount'))['total'] or 0
        return total_budget - total_spent

class CategoryBudget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    monthly_budget = models.ForeignKey('MonthlyBudget', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[validate_positive_amount, validate_currency_format])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['monthly_budget', 'category']
        ordering = ['category__name']

    def __str__(self):
        return f"{self.category.name} - ₹{self.amount} ({self.monthly_budget.month}/{self.monthly_budget.year})"

    @property
    def total_spent(self):
        """Calculate total spent in this category for the budget's month"""
        start_date = timezone.datetime(self.monthly_budget.year, self.monthly_budget.month, 1).date()
        if self.monthly_budget.month == 12:
            end_date = timezone.datetime(self.monthly_budget.year + 1, 1, 1).date()
        else:
            end_date = timezone.datetime(self.monthly_budget.year, self.monthly_budget.month + 1, 1).date()

        return Expense.objects.filter(
            user=self.user,
            category=self.category,
            date__gte=start_date,
            date__lt=end_date
        ).aggregate(total=models.Sum('amount'))['total'] or 0

    @property
    def remaining_budget(self):
        """Calculate remaining budget for this category"""
        return self.amount - self.total_spent

    @property
    def budget_percentage(self):
        """Calculate percentage of budget used"""
        if self.amount > 0:
            return (self.total_spent / self.amount) * 100
        return 0

class MonthlyBudget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    year = models.IntegerField(default=timezone.now().year)
    month = models.IntegerField(default=timezone.now().month)
    total_budget = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    income = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    savings_target = models.DecimalField(max_digits=5, decimal_places=2, default=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'year', 'month']
        ordering = ['-year', '-month']

    def __str__(self):
        return f"{self.user.username}'s Budget for {self.month}/{self.year}"

    @property
    def target_expenses(self):
        """Calculate target expenses based on income and savings target"""
        if self.income > 0:
            return self.income * (1 - self.savings_target / 100)
        return 0

    @property
    def total_spent(self):
        """Calculate total spent across all categories for this month"""
        start_date = timezone.datetime(self.year, self.month, 1).date()
        if self.month == 12:
            end_date = timezone.datetime(self.year + 1, 1, 1).date()
        else:
            end_date = timezone.datetime(self.year, self.month + 1, 1).date()

        return Expense.objects.filter(
            user=self.user,
            date__gte=start_date,
            date__lt=end_date
        ).aggregate(total=models.Sum('amount'))['total'] or 0

    @property
    def remaining_budget(self):
        """Calculate remaining budget for this month"""
        return self.total_budget - self.total_spent

    @property
    def budget_percentage(self):
        """Calculate percentage of budget used"""
        if self.total_budget > 0:
            return (self.total_spent / self.total_budget) * 100
        return 0

    def get_category_budgets(self):
        """Get all category budgets for this month"""
        return CategoryBudget.objects.filter(monthly_budget=self)

    def set_category_budget(self, category, amount):
        """Set or update budget for a specific category"""
        return CategoryBudget.objects.update_or_create(
            monthly_budget=self,
            category=category,
            defaults={'amount': amount, 'user': self.user}
        )

class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='budget_entries')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[validate_positive_amount, validate_budget_limit, validate_currency_format])
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ['user', 'category']

    def __str__(self):
        return f"{self.category.name} - ${self.amount}"

class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[validate_positive_amount, validate_currency_format])
    description = models.CharField(max_length=200)
    date = models.DateField(validators=[validate_future_date])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.description} - ${self.amount}"

    def clean(self):
        super().clean()
        current_date = timezone.now().date()
        if self.date and self.date > current_date:
            raise ValidationError({'date': 'Expense date cannot be in the future.'})
        if self.category and self.amount > self.category.remaining_budget:
            raise ValidationError({'amount': 'Set a budget before adding an expense.'})

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
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[validate_positive_amount, validate_currency_format])
    description = models.TextField(blank=True)
    date = models.DateField(validators=[validate_future_date])
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

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type.capitalize()} - Rs. {self.amount}"

@receiver(post_save, sender=User)
def create_default_categories(sender, instance, created, **kwargs):
    if created:
        for category_name, color in DEFAULT_CATEGORIES.items():
            Category.objects.create(
                name=category_name,
                color=color,
                icon=DEFAULT_CATEGORY_ICONS.get(category_name, 'receipt')
            )
