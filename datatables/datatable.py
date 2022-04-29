import json

from datetime import datetime

from django.template.loader import render_to_string
from django.contrib.admin.utils import get_fields_from_path
from django.db import models
from django.core.paginator import Paginator
from django.utils.timezone import get_current_timezone

from .datatable_filters import FieldListFilter, DateTimeFieldListFilter
from .utils import (
    label_for_field,
    format_datetime,
)


class Datatable:
    template = 'datatables/_datatable.html'
    table_template = 'datatables/table.html'
    filter_template = 'datatables/filters.html'
    export_template = 'datatables/export.html'
    toggle_template = 'datatables/toggle-columns.html'
    config = {}

    def __init__(
            self,
            request,
            model,
            view,
            columns,
            update_interval,
            filters=[],
            filter_lookup=[],
            ordering=[],
            search_fields=[],
            table_search_fields=[],
            config={},
            show_columns=True,
    ):
        self.request = request
        self.model = model
        self.view = view
        self.columns = columns
        self._filters = filters
        self.filter_lookup = filter_lookup
        self.lookup_opts = []
        if model:
            self.lookup_opts = [f.name for f in model._meta.get_fields()]

        self.filter_specs = self.get_filters()
        self.ordering = ordering
        self.search_fields = search_fields
        self.table_search_fields = table_search_fields
        self.config = config
        self.show_columns = show_columns
        self.update_interval = update_interval
        self.exportable = view.exportable

    def __str__(self):
        return render_to_string(self.template, self.get_context())

    def get_context(self):
        return {
            'id': self.get_id(),
            'datatable': self,
            'columns': self.get_columns(),
            'config': self.get_config(),
        }

    def table(self):
        return render_to_string(self.table_template, self.get_context())

    def filters(self):
        return render_to_string(self.filter_template, self.get_context())

    def export_button(self):
        return render_to_string(self.export_template, self.get_context())

    def toggle_columns(self):
        return render_to_string(self.toggle_template, self.get_context())

    def get_id(self):
        return id(self)

    def get_columns(self):
        return self.get_table_columns()

    def get_config(self):
        return json.dumps(self.config)

    def get_filters(self):
        self.filter_specs = {}
        for list_filter, *settings in self._filters:
            try:
                settings = dict(settings)
            except ValueError:
                settings = {}

            field_path = None
            field, field_list_filter_class = list_filter, FieldListFilter.create
            if not isinstance(field, models.Field):
                # For annotated data you have to specify the type
                if 'field_type' in settings:
                    # No path for annotated fields
                    field_path = list_filter
                    field = settings['field_type']()
                else:
                    field_path = field
                    field = get_fields_from_path(self.model, field_path)[-1]

            spec = field_list_filter_class(
                field, self.model, field_path=field_path,
                **settings,
            )
            if spec and spec.has_output():
                self.filter_specs[list_filter] = spec

        return self.filter_specs.values()

    def serialize(self, qs):
        page, page_size = self.parse_page_info()
        pager = Paginator(qs, page_size)
        return {
            "recordsTotal": self.total,
            "recordsFiltered": pager.count,
            "data": self.serialize_data(pager.page(page)),
        }

    def serialize_data(self, data):
        result = []
        for item in data:
            obj = {}
            columns = self.columns
            for column in columns:
                if isinstance(column, tuple):
                    column = column[0]

                obj[column] = self.get_column_value(item, column)

            result.append(obj)

        return result

    def get_column_value(self, item, column, raw=False):
        if isinstance(column, tuple):
            column = column[0]
        if hasattr(self.view, column):
            view_func = getattr(self.view, column)
            attr = view_func(item)
        elif '__' in column:
            fields = column.split("__")
            attr = item
            for field in fields:
                attr = self._get_attr(attr, field)
        else:
            attr = self._get_attr(item, column)

        if isinstance(attr, datetime):
            attr = attr.astimezone(get_current_timezone())
            if raw:
                attr = f'{attr.strftime("%Y-%m-%d %H:%M")}'
            else:
                attr = format_datetime(attr)

        if attr is None:
            attr = '-'

        return str(attr)

    def _get_attr(self, item, column):
        if hasattr(item, f'get_{column}_display'):
            attr = getattr(item, f'get_{column}_display')()
        elif hasattr(item, column):
            attr = getattr(item, column)
        else:
            attr = ''

        return attr

    def get_orderable_columns(self):
        available = self.lookup_opts
        if self.model:
            available += list(self.view.get_queryset().query.annotation_select)
        return available

    def get_queryset(self):
        qs = self.view.get_queryset()
        self.total = qs.count()
        filters = self.parse_filters()

        filters &= self.parse_search()
        qs = qs.filter(filters)
        ordering = self.parse_ordering()
        qs = qs.order_by(*ordering)
        return qs.distinct()

    def _create_search_query(self, fields, search):
        q = models.Q()
        for search_field in fields:
            q |= models.Q(**{f'{search_field}__icontains': search})

        return q

    def parse_search(self):
        search = self.request.GET.get('main_search')
        table_search = self.request.GET.get('search[value]')
        query = models.Q()
        if search:
            query &= self._create_search_query(self.search_fields, search)
        if table_search:
            query &= self._create_search_query(self.search_fields, table_search)
        return query

    def parse_filters(self):
        filters = [i.split("=") for i in self.request.GET.getlist('filters[]') if len(i.split("=")) == 2]
        args = {}
        for f, a in filters:
            if '__in' in f or '__overlap' in f:
                tmp = args.get(f, [])
                if a in self.filter_lookup:
                    a = self.filter_lookup.get(a)
                    tmp.extend(a)
                else:
                    tmp.append(a)
                args[f] = tmp
            elif DateTimeFieldListFilter.contains_valid_predicate(f):
                date, time = a.split(' ')
                year, month, day = date.split('-')
                hour, _ = time.split(':')
                args[f] = datetime(int(year), int(month), int(day), int(hour))
            else:
                args[f] = a

        query = models.Q()
        for f in args:
            query &= models.Q(**{f: args[f]})

        for f in self.view.get_filters():
            query &= models.Q(**f)

        return query

    def parse_page_info(self):
        page_size = int(self.request.GET.get("length", 25))
        page = int(self.request.GET.get("start", 0)) / page_size
        return (page + 1, page_size)

    def parse_ordering(self):
        sort_cols = self.ordering
        for i in range(0, len(self.columns)):
            sort_col = self.request.GET.get(f'order[{i}][column]')
            if sort_col is None:
                return sort_cols
            sort_col = int(sort_col)
            col = self.columns[sort_col]
            if isinstance(col, tuple):
                col = col[0]
            sort_dir = '-' if self.request.GET.get(f'order[{i}][dir]') == 'desc' else ''
            sort_col_name = sort_dir + col
            sort_cols.append(sort_col_name)

        return sort_cols

    def get_table_columns(self):
        """
        Generate the list column headers.
        """
        columns = []
        orderable = self.get_orderable_columns()
        for field_name in self.columns:
            visible = True
            togglable = False
            if isinstance(field_name, tuple):
                try:
                    settings = field_name[2]
                    visible = settings.get('visible', True)
                    togglable = settings.get('togglable', False)
                except IndexError:
                    pass
                label = field_name[1]
                field_name = field_name[0]
            else:
                label = label_for_field(field_name, self.model, self.view)

            columns.append((label, field_name, field_name in orderable, visible, togglable))

        return columns
