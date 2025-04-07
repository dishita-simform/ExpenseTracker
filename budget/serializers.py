from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Expense, Category, Budget

class UserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'date_joined', 'last_login')
        read_only_fields = ('id', 'date_joined', 'last_login')

class CategorySerializer(serializers.ModelSerializer):
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    remaining_budget = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Category
        fields = ('id', 'name', 'description', 'icon', 'color', 'budget', 'is_active', 
                 'total_spent', 'remaining_budget', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Expense
        fields = ('id', 'user', 'category', 'category_name', 'amount', 'description', 'date', 'created_at', 'updated_at')
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Expense must be greater than zero.")
        return value

    def validate_category(self, value):
        if not Category.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Invalid category.")
        return value

    def validate_description(self, value):
        if len(value) < 10:
            raise serializers.ValidationError("Description must be at least 10 characters long.")
        return value

    def validate_date(self, value):
        from datetime import date
        if value > date.today():
            raise serializers.ValidationError("Date cannot be in the future.")
        return value

class BudgetSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    remaining_budget = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Budget
        fields = ('id', 'category', 'category_name', 'amount', 'month', 'year', 
                 'total_spent', 'remaining_budget', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
