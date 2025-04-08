from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

def validate_positive_amount(value):
    """Validate that the amount is positive."""
    if value <= 0:
        raise ValidationError('Amount must be greater than zero.')

def validate_future_date(value):
    """Validate that the date is not in the future."""
    if value > timezone.now().date():
        raise ValidationError('Date cannot be in the future.')

def validate_budget_limit(value):
    """Validate that the budget limit is reasonable."""
    if value > 1000000:  # 1 million
        raise ValidationError('Budget limit seems unreasonably high. Please verify.')

def validate_percentage(value):
    """Validate that the value is a percentage between 0 and 100."""
    if not 0 <= value <= 100:
        raise ValidationError('Percentage must be between 0 and 100.')

def validate_currency_format(value):
    """Validate that the currency format is correct."""
    try:
        Decimal(str(value))
    except:
        raise ValidationError('Invalid currency format.') 