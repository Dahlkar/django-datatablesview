import csv
from datetime import datetime
from django.http import (
    JsonResponse,
    StreamingHttpResponse,
)
from django.views.generic import TemplateView
from .datatable import Datatable
from .utils import PassThroughWriter


class DatatableView(TemplateView):
    template_name = 'datatables/datatable.html'
    model = None
    columns = None
    list_filters = None
    filter_lookup = None
    ordering = None
    search_fields = None
    table_search_fields = None
    table_config = None
    lookup_opts = None
    filters = None
    exportable = False
    update_interval = 60000  # Milliseconds

    def dispatch(self, request, *args, **kwargs):
        self.init_datatable(request, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def init_datatable(self, request, **kwargs):
        self.datatable = Datatable(
            request,
            self.model,
            self,
            self.get_columns(),
            self.get_update_interval(),
            self.get_list_filters(),
            self.get_filter_lookup(),
            self.get_ordering(),
            self.get_search_fields(),
            self.get_table_search_fields(),
            self.get_table_config(**kwargs),
        )
        if self.lookup_opts:
            self.datatable.lookup_opts = self.lookup_opts
        return self.datatable

    def get_columns(self):
        return self.columns or []

    def get_update_interval(self):
        return self.update_interval

    def get_export_columns(self):
        return self.request.GET.getlist('visible[]')

    def get_list_filters(self):
        return self.list_filters or []

    def get_filter_lookup(self):
        return self.filter_lookup or {}

    def get_ordering(self):
        return self.ordering or []

    def get_filters(self):
        return self.filters or []

    def get_search_fields(self):
        return self.search_fields or []

    def get_table_search_fields(self):
        return self.table_search_fields or []

    def get_table_config(self, **kwargs):
        return self.table_config or {}

    def get_queryset(self):
        qs = self.model.objects.all()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['main_search'] = self.request.GET.get('main_search', '')
        context['datatable'] = self.datatable
        return context

    def render_to_json_response(self):
        data = self.get_data()
        return JsonResponse(self.datatable.serialize(data))

    def download_as_csv(self):
        def csv_row_generator(query_set):
            writer = csv.writer(PassThroughWriter())
            headers = [c[1] if isinstance(c, tuple) else c for c in self.get_export_columns()]

            yield writer.writerow(headers)

            for obj in query_set:
                row = [self.datatable.get_column_value(obj, c, raw=True) for c in self.get_export_columns()]
                yield writer.writerow(row)

        query_set = self.get_data()
        response = StreamingHttpResponse(csv_row_generator(query_set), content_type='text/csv')
        filename = self.model._meta.verbose_name_plural + "_{:%Y-%m-%dT%H-%M}".format(datetime.now())
        filename = filename.replace(' ', '_')
        response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
        return response

    def get_data(self):
        return self.datatable.get_queryset()

    def get(self, request, *args, **kwargs):
        if request.GET.get('format') == 'json':
            return self.render_to_json_response()
        elif request.GET.get('format') == 'csv':
            return self.download_as_csv()
        else:
            context = self.get_context_data()
            return self.render_to_response(context)
