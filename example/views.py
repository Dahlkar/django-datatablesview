from django.urls import reverse
from django.utils.html import format_html
from django.views import generic

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
        'education',
        ('pk', None, {"visible": False}),
    ]
    list_filters = [
        ('job',),
        ('date_of_birth',
         ('title', 'Date of birth'),
         ('endpoints', [
             {'label': 'From', 'predicate': 'gte'},
             {'label': 'To', 'predicate': 'lte'}
         ])
         ),
        ('education',
         ('choices', (
             ('Elementary', [
                 ('Preschool', 'Preschool'),
                 ('Middle school', 'Middle school'),
                 ('High school', 'High school')]),
             ('Collage', [
                 ('Bachelor', 'Bachelor'),
                 ('Masters', 'Masters'),
                 ('Doctorate', 'Doctorate')]
              ))),
            ('grouped_choices', True)
         )
    ]
    search_fields = [
        'first_name',
        'last_name',
    ]
    exportable = True
    table_config = {
        "language": {
            "paginate": {
                "next": "n",
            }
        },
        "rowId": 'pk',
        "select": 'multi',
    }
    paginate_by = 1

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
