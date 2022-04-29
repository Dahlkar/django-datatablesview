from urllib.parse import urlencode

from django.contrib.admin.utils import get_model_from_relation
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils.translation import gettext_lazy as _


class ListFilter:
    title = None  # Human-readable title to appear in the right sidebar.
    template = 'admin/filter.html'

    def __init__(self, model):
        # This dictionary will eventually contain the request's query string
        # parameters actually used by this filter.
        if self.title is None:
            raise ImproperlyConfigured(
                "The list filter '%s' does not specify a 'title'."
                % self.__class__.__name__
            )

    def has_output(self):
        """
        Return True if some choices would be output for this filter.
        """
        raise NotImplementedError('subclasses of ListFilter must provide a has_output() method')

    def choices(self, changelist):
        """
        Return choices ready to be output in the template.
        `changelist` is the ChangeList to be displayed.
        """
        raise NotImplementedError('subclasses of ListFilter must provide a choices() method')

    def expected_parameters(self):
        """
        Return the list of parameter names that are expected from the
        request's query string and that will be used by this filter.
        """
        raise NotImplementedError('subclasses of ListFilter must provide an expected_parameters() method')


class FieldListFilter(ListFilter):
    _field_list_filters = []
    _take_priority_index = 0

    def __init__(self, field, model, field_path):
        self.field = field
        self.field_path = field_path
        self.title = getattr(field, 'verbose_name', field_path)
        # If the field has a verbose_name field but no value
        # capitalize the field_path
        if self.title is None:
            self.title = field_path.capitalize()
        super().__init__(model)

    def has_output(self):
        return True

    @classmethod
    def register(cls, test, list_filter_class, take_priority=False):
        if take_priority:
            # This is to allow overriding the default filters for certain types
            # of fields with some custom filters. The first found in the list
            # is used in priority.
            cls._field_list_filters.insert(
                cls._take_priority_index, (test, list_filter_class))
            cls._take_priority_index += 1
        else:
            cls._field_list_filters.append((test, list_filter_class))

    @classmethod
    def create(cls, field, model, field_path, **settings):
        for test, list_filter_class in cls._field_list_filters:
            if test(field):
                return list_filter_class(
                    field, model, field_path=field_path, **settings)


class RelatedFieldListFilter(FieldListFilter):
    def __init__(self, field, model, field_path, **settings):
        other_model = get_model_from_relation(field)
        self.lookup_kwarg = '%s__%s__in' % (field_path, field.target_field.name)
        self.lookup_kwarg_isnull = '%s__in' % field_path
        super().__init__(field, model, field_path)

        if settings.get('choices'):
            self.lookup_choices = settings.get('choices')
        else:
            self.lookup_choices = self.field_choices(field)

        if settings.get('title'):
            self.title = settings.get('title')
        elif hasattr(field, 'verbose_name'):
            self.title = field.verbose_name.capitalize()
        else:
            self.title = other_model._meta.verbose_name.capitalize()

    def has_output(self):
        return len(self.lookup_choices) > 1

    def expected_parameters(self):
        return [self.lookup_kwarg, self.lookup_kwarg_isnull]

    def field_choices(self, field):
        return field.get_choices(include_blank=False)

    def choices(self):
        for pk_val, val in self.lookup_choices:
            yield {
                'query_string': urlencode({self.lookup_kwarg: pk_val}),
                'display': val,
            }


FieldListFilter.register(lambda f: f.remote_field, RelatedFieldListFilter)


class BooleanFieldListFilter(FieldListFilter):
    def __init__(self, field, model, field_path, **settings):
        self.lookup_kwarg = '%s__in' % field_path
        super().__init__(field, model, field_path)

        if settings.get('choices'):
            self.lookup_choices = settings.get('choices')
        else:
            self.lookup_choices = (
                ('1', _('Yes')),
                ('0', _('No')))

        if settings.get('title'):
            self.title = settings.get('title')
        elif hasattr(field, 'verbose_name'):
            self.title = field.verbose_name.capitalize()

    def expected_parameters(self):
        return [self.lookup_kwarg]

    def choices(self):
        for lookup, title in self.lookup_choices:
            yield {
                'query_string': urlencode({self.lookup_kwarg: lookup}),
                'display': title,
            }
        if self.field.null:
            yield {
                'query_string': urlencode({self.lookup_kwarg2: 'True'}),
                'display': _('Unknown'),
            }


FieldListFilter.register(lambda f: isinstance(f, models.BooleanField), BooleanFieldListFilter)


class ChoicesFieldListFilter(FieldListFilter):
    def __init__(self, field, model, field_path, **settings):
        self.lookup_kwarg = '%s__in' % field_path
        super().__init__(field, model, field_path)
        self.checked = []

        if settings.get('choices'):
            self.lookup_choices = settings.get('choices')
        else:
            self.lookup_choices = self.field.flatchoices

        if settings.get('title'):
            self.title = settings.get('title')
        elif hasattr(field, 'verbose_name'):
            self.title = field.verbose_name.capitalize()

        if settings.get('checked'):
            self.checked = settings.get('checked')

        self.has_grouped_choices = settings.get('grouped_choices', False)

    def expected_parameters(self):
        return [self.lookup_kwarg, self.lookup_kwarg_isnull]

    def choices(self, choices=None):
        if not choices:
            choices = self.lookup_choices

        for lookup, title in choices:
            if lookup is None:
                continue

            yield {
                'query_string': urlencode({self.lookup_kwarg: lookup}),
                'display': title,
                'checked': lookup in self.checked,
                'val': lookup,
            }

    def grouped_choices(self):
        for group, choices in self.lookup_choices:
            yield {
                'display': group,
                'checked': group in self.checked,
            }, self.choices(choices)


FieldListFilter.register(lambda f: bool(f.choices), ChoicesFieldListFilter)
FieldListFilter.register(lambda f: isinstance(f, models.CharField), ChoicesFieldListFilter)

try:
    from django.contrib.postgres.fields import ArrayField
except ModuleNotFoundError:
    pass
else:
    class ArrayFieldListFilter(FieldListFilter):
        def __init__(self, field, model, field_path, **settings):
            self.lookup_kwarg = '%s__overlap' % field_path
            self.lookup_kwarg_isnull = '%s__len' % field_path
            super().__init__(field, model, field_path)

            if settings.get('choices'):
                self.lookup_choices = settings.get('choices')
            else:
                self.lookup_choices = [(f'{choice}', title) for choice, title
                                       in self.field.base_field.flatchoices]

            self.empty_value_display = 'None'

            if settings.get('title'):
                self.title = settings.get('title')
            elif hasattr(field, 'verbose_name'):
                self.title = field.verbose_name.capitalize()

        def expected_parameters(self):
            return [self.lookup_kwarg, self.lookup_kwarg_isnull]

        def choices(self):
            for lookup, title in self.lookup_choices:
                if lookup is None:
                    continue
                yield {
                    'query_string': urlencode({self.lookup_kwarg: lookup}),
                    'display': title,
                }

            yield {
                'query_string': urlencode({self.lookup_kwarg_isnull: '0'}),
                'display': self.empty_value_display,
            }


    FieldListFilter.register(lambda f: isinstance(f, ArrayField), ArrayFieldListFilter)


class DateTimeFieldListFilter(FieldListFilter):
    def __init__(self, field, model, field_path, **settings):
        super().__init__(field, model, field_path)
        self.lookup_kwarg = '%s__' % field_path
        self._endpoints = settings.get('endpoints')

        if settings.get('title'):
            self.title = settings.get('title')
        elif hasattr(field, 'verbose_name'):
            self.title = field.verbose_name.capitalize()
        self.is_date = True

    @staticmethod
    def valid_predicates():
        return ['gte', 'lte', 'gt', 'lt']

    @classmethod
    def contains_valid_predicate(cls, f):
        return any(i for i in cls.valid_predicates() if i in f)

    def endpoints(self):
        for endpoint in self._endpoints:
            yield {
                'lookup': self.lookup_kwarg + endpoint['predicate'],
                'display': endpoint['label']
            }

    def choices(self, changelist):
        yield {}

    def expected_parameters(self):
        return []


FieldListFilter.register(lambda f: isinstance(f, models.DateField), DateTimeFieldListFilter)
FieldListFilter.register(lambda f: isinstance(f, models.DateTimeField), DateTimeFieldListFilter)
