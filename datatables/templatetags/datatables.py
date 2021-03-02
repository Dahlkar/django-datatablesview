from django import template

register = template.Library()


@register.inclusion_tag('datatables/css.html')
def css_bundle():
    return {}


@register.inclusion_tag('datatables/js.html')
def js_bundle():
    return {}
