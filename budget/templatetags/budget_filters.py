from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def div(value, arg):
    """Divide the value by the argument"""
    try:
        if value is None or arg is None:
            return 0
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def mul(value, arg):
    """Multiply the value by the argument"""
    try:
        if value is None or arg is None:
            return 0
        return float(value) * float(arg)
    except ValueError:
        return 0

@register.filter
def sub(value, arg):
    """Subtract the argument from the value"""
    try:
        if value is None or arg is None:
            return 0
        return float(value) - float(arg)
    except ValueError:
        return 0

@register.filter
def abs_value(value):
    """Returns the absolute value of a number."""
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return value

@register.filter
def get(dictionary, key):
    """
    Gets a value from a dictionary using the key.
    Usage: {{ dictionary|get:key }}
    """
    return dictionary.get(key, []) 