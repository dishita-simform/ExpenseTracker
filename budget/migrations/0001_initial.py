# Generated by Django 5.0.2 on 2025-04-16 14:02

import budget.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('icon', models.CharField(default='receipt', max_length=50)),
                ('color', models.CharField(default='primary', max_length=50)),
            ],
            options={
                'verbose_name_plural': 'Categories',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Expense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, validators=[budget.validators.validate_positive_amount, budget.validators.validate_currency_format])),
                ('description', models.CharField(max_length=200)),
                ('date', models.DateField(validators=[budget.validators.validate_future_date])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='budget.category')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='IncomeSource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('icon', models.CharField(default='money-bill-wave', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Income',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, validators=[budget.validators.validate_positive_amount, budget.validators.validate_currency_format])),
                ('description', models.TextField(blank=True)),
                ('date', models.DateField(validators=[budget.validators.validate_future_date])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='budget.incomesource')),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='MonthlyBudget',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField(default=2025)),
                ('month', models.IntegerField(default=4)),
                ('total_budget', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('income', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('savings_target', models.DecimalField(decimal_places=2, default=20, max_digits=5)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-year', '-month'],
                'unique_together': {('user', 'year', 'month')},
            },
        ),
        migrations.CreateModel(
            name='Budget',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, validators=[budget.validators.validate_positive_amount, budget.validators.validate_budget_limit, budget.validators.validate_currency_format])),
                ('start_date', models.DateField(default=django.utils.timezone.now)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='budget_entries', to='budget.category')),
            ],
            options={
                'unique_together': {('user', 'category')},
            },
        ),
        migrations.CreateModel(
            name='CategoryBudget',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, validators=[budget.validators.validate_positive_amount, budget.validators.validate_currency_format])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='budget.category')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('monthly_budget', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='budget.monthlybudget')),
            ],
            options={
                'ordering': ['category__name'],
                'unique_together': {('monthly_budget', 'category')},
            },
        ),
    ]
