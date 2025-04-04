from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import ValidationError
from .constants import CATEGORIES

class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default='receipt')  # FontAwesome icon name
    color = models.CharField(max_length=50, default='primary')  # Bootstrap color name
    budget = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Monthly budget amount

    class Meta:
        verbose_name_plural = 'Categories'
        unique_together = ['user', 'name']

    def __str__(self):
        return self.name

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
