# apps/payments/templatetags/query_transform.py
from django import template

register = template.Library()

@register.simple_tag
def query_transform(request, **kwargs):
    """
    Returns the current URL with modified query parameters.
    Usage: {% query_transform request page=page_obj.next_page_number %}
    """
    updated = request.GET.copy()
    for key, value in kwargs.items():
        if value is not None:
            updated[key] = value
        else:
            updated.pop(key, None)
    return updated.urlencode()