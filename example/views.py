from django.views import generic
from django.utils.html import format_html
from django.urls import reverse
from datatables.views import DatatableView
from .models import Person


class PersonTable(DatatableView):
    header = 'Persons'
    model = Person
    columns = [
        'first_name',
        'last_name',
        ('date_of_birth', 'Birthday', {"togglable": True, "visible": False}),
        'age',
        'job',
    ]
    list_filters = [
        ('job',),
    ]
    search_fields = [
        'first_name',
        'last_name',
    ]
    exportable = True

    def first_name(self, obj):
        if self.request.GET.get('format') == 'csv':
            return obj.first_name

        return format_html(
            '<a href="{}">{}</a>',
            reverse('person-detail', kwargs={'pk': obj.pk}),
            obj.first_name,
        )


class PersonDetail(generic.DetailView):
    model = Person
