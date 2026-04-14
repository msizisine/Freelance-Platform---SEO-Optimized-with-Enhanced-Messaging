from django import template
from datetime import timedelta

register = template.Library()

@register.simple_tag
def change_list_object_tools():
    """
    Empty implementation to avoid Django admin template errors.
    """
    return ""

@register.filter
def add_days(value, days):
    """
    Adds specified number of days to a date value.
    """
    try:
        return value + timedelta(days=int(days))
    except (AttributeError, ValueError, TypeError):
        return value
