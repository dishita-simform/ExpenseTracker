from rest_framework import serializers
from .models import Expense

CATEGORIES = ['Rent', 'Food', 'Travel', 'Bills', 'Entertainment', 'Other']

class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = '__all__'

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Expense must be greater than zero.")
        return value

    def validate_category(self, value):
        if value not in CATEGORIES:
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
