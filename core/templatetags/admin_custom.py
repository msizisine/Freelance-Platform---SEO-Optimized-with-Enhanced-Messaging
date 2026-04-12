from django import template

register = template.Library()

@register.simple_tag
def change_list_object_tools():
    """
    Empty implementation to avoid Django admin template errors.
    """
    return ""
