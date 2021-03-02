from datetime import (
    datetime,
    timedelta,
)
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.utils.timezone import get_current_timezone
from django.forms.utils import pretty_name
from django.contrib.admin.utils import FieldIsAForeignKeyColumnName
from django.core.exceptions import (
    FieldDoesNotExist,
)


class PassThroughWriter:
    """ Can be used with StreamingHttpResponse to avoid buffering. """
    def write(self, value):
        return value


def init_kwargs(model, arg_dict):
    model_fields = [f.name for f in model._meta.get_fields()]
    return {k: v for k, v in arg_dict.items() if k in model_fields}


def label_for_field(name, model, view=None, return_attr=False):
    """
    Return a sensible label for a field name. The name can be a callable,
    property (but not created with @property decorator), or the name of an
    object's attribute, as well as a model field. If return_attr is True, also
    return the resolved attribute (which could be a callable). This will be
    None if (and only if) the name refers to a field.
    """
    attr = None
    if '__' in name:
        names = name.split('__')
        model_names = names[:-1]
        for name in model_names:
            model = model._meta.get_field(name).related_model

        field_name = names[-1]
        related_field = model._meta.get_field(field_name)

        label = related_field.verbose_name
        attr = str
    else:
        try:
            field = model._meta.get_field(name)
            try:
                label = field.verbose_name
            except AttributeError:
                # field is likely a ForeignObjectRel
                label = field.related_model._meta.verbose_name
        except FieldDoesNotExist:
            if name == "__str__":
                label = str(model._meta.verbose_name)
                attr = str
            else:
                if callable(name):
                    attr = name
                elif hasattr(view, name):
                    attr = getattr(view, name)
                elif hasattr(model, name):
                    attr = getattr(model, name)
                else:
                    label = name

                if hasattr(attr, "short_description"):
                    label = attr.short_description
                elif (isinstance(attr, property) and
                      hasattr(attr, "fget") and
                      hasattr(attr.fget, "short_description")):
                    label = attr.fget.short_description
                elif callable(attr):
                    if attr.__name__ == "<lambda>":
                        label = "--"
                    else:
                        label = pretty_name(attr.__name__)
                else:
                    label = pretty_name(name)
        except FieldIsAForeignKeyColumnName:
            label = pretty_name(name)
            attr = name

    if return_attr:
        return (label, attr)
    else:
        return label


def format_datetime(d):
    return f'{d.strftime("%Y-%m-%d %H:%M")} ({naturaltime(d)})'
