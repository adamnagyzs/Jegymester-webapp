from django import template

register = template.Library()


@register.filter
def to_range(value):
    """Convert an integer to a range list: {{ 10|to_range }} → [1, 2, ..., 10]"""
    try:
        return range(1, int(value) + 1)
    except (ValueError, TypeError):
        return []
