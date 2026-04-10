import json
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name='to_json')
def to_json(value):
    """Convert Python dict/list to valid JSON for use in JavaScript."""
    return mark_safe(json.dumps(value))
