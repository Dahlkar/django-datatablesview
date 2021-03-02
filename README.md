# Datatables
Datatables is a Django app that which gives the possibility to create
views that integrates with the jQuery javascript library DataTables.

It also includes some features which makes it possible to export data to a csv
from the table.


## Installation
Add `'datatables'` to your `INSTALLED_APPS` setting like this:

``` python
    INSTALLED_APPS = [
        ...
        'datatables',
    ]
```

## Usage

1. Create a view:
``` python
from datatables.views import DatatableView
from someapp.models import MyModel


class ExampleView(DatatableView):
    model = MyModel
    columns = [
        'field1',
        'field2',
        'custom_data',
    ]

    def custom_data(self, obj):
        return 'some custom data'
```

2. Add css and js to template:
`example.html`
``` html
{% load datatables %}

<html>
    <head>
    {% css_bundle %}
    </head>
    <body>
    {{ datatable }}
    </body>
    {% js_bundle %}
</html>
```
