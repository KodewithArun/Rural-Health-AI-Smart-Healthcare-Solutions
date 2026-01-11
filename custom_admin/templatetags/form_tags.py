from django import template

register = template.Library()


@register.inclusion_tag("custom_admin/includes/form_field_errors.html")
def field_errors(field):
    """Display form field errors"""
    return {"field": field}
