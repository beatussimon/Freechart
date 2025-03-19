from django import template

register = template.Library()

@register.filter
def endswith(value, arg):
    """Check if a string ends with a given suffix."""
    if value is None or not isinstance(value, str):
        return False
    return value.endswith(arg)