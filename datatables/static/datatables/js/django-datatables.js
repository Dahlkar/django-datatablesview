$('document').ready(function(){
    const dataTables = document.getElementsByClassName('data-table');
    Object.values(dataTables).forEach((table) => {
        datatableify(table);
    });
});


function datatableify(table) {
    const datatable = $(table);
    const id = datatable.data('id');
    const default_settings = {
        serverSide: true,
        paging: true,
        pageLength: 25,
        info: true,
        ordering: true,
        searching: true,
        columnDefs: [
            { className: "table__cell", targets: "_all" },
            { visible: false, targets: "hidden" },
        ],
        dom: 'rti<"pagination"p>',
        ajax: {
            url: "?format=json",
            data: d => {
                var searchstring = $("form:eq(0) :input").val();
                if (searchstring)
                    d["main_search"] = searchstring;
                d["filters"] = [];
                $(".datatable-filters."+id+" input:checkbox:checked.datatable-filter").each(function() {
                    d["filters"].push(this.name);
                });
                $(".datatable-filters."+id+" input:radio:checked.datatable-filter").each(function() {
                    d["select"] = this.value
                });
                d["visible"] = [];
                $(".table__header th:visible").each(function () {
                    d["visible"].push($(this).attr('name'));
                });
            },
        },
        createdRow: function(row, data, dataIndex) {
            $(row).addClass("table__row");
            $(row).addClass(data.html_class);
        },
    }
    let data_func = default_settings.ajax.data;
    const settings = Object.assign(default_settings, datatable.data('config'));
    settings.ajax.data = data_func;
    var table = datatable.DataTable(settings);

    $('.datatable-filter.'+id).on('change', function(){
        var className = 'input:checkbox:checked.'+this.className.split(" ").join('.');
        var checked = $(className);
        var group = $(this).data('group');
        if (group) {
            $('#'+group).prop('checked', checked.length> 0);
        }
        table.draw();
    });

    $('.datatable-filter-group.' + id).on('change', function(){
        var group = this.id;
        $('.datatable-filter.' + group + '.' + id).prop('checked', this.checked);
        table.draw();
    });
    $('.datatable-filters.' + id).append($('#DataTables_Table_0_filter'));
    $('.dataTables_filter input').addClass('form-control');
    $('.dataTables_filter input').attr('placeholder', 'Sök');
    if (settings.main_searching) {
        $('form:eq(0)').submit(function (e) {
            e.preventDefault();
            table.draw();
        });
    }
    $('.csv-button.'+id).click(function(e){
        var params = table.ajax.params();
        var href = "?format=csv&" + $.param(params);
        $(this).attr("href", href);
    });
    $('.toggle-column.' + id).on('change', function (e) {
        var column = table.column('#' + $(this).attr('data-column'));
        column.visible(!column.visible());
        table.draw();
    });
    if(datatable.data('update-interval')) {
        setInterval(function () {
            table.draw();
        }, datatable.data('update-interval'));
    }
}
