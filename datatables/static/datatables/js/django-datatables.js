$('document').ready(function(){
    let tableList = {}
    $(".data-table").each(function(){
        const tableSelector = $(this);
        const tableId = tableSelector.data('id');
        tableList[tableId] = {'visible': false,'table': null};
    });

    setInterval(function(){
        $(".data-table")
            .each(function(){ // Remove tables that is hidden
                const tableSelector = $(this);
                const newId = tableSelector.data('id');
                const tableEntry = tableList[newId];
                if(!tableSelector.is(':visible') && tableEntry.visible){
                    tableEntry.visible = false;
                    tableEntry.table && tableEntry.table.destroy();
                    $('.datatable-filters.' + newId + ' #DataTables_Table_0_filter').remove();
                }})
            .each(function(index){ // Add tables that is visible
                const tableSelector = $(this);
                const tableElement = tableSelector[0];
                const newId = tableSelector.data('id');
                const tableEntry = tableList[newId];
                if(tableSelector.is(':visible') && !tableEntry.visible){
                    tableEntry.visible = true;
                    tableEntry.table = datatableify(tableElement, index);
                }
            });
    }, 50);
});

function getContextFromUrl() {
    // Table context format: table<index>{<contextData>}
    let urlFragment = decodeURI(new URL(document.URL).hash).substring(1);
    return {
        urlFragment: urlFragment,
        matchedGroups: [...urlFragment.matchAll(/table([\d]){(.*?)}/g)]
            .reduce((acc, elem) => {
                return {...acc, [elem[1]]: elem[2]}
            }, {})
    }
}

function buildUrlFragment(index, d) {
    const page = d['start'] / d['length']
    const filters = d['filters'].join("&filter[]=")
    const search = d['search']['value']
    const order = d['order'].length > 0 ?
        `&order_col=${d['order'][0]['column']}` +
        `&order_dir=${d['order'][0]['dir']}` : ''

    const context = getContextFromUrl();
    const contextData = `page=${page}${order}`+
        (search ? `&search=${search}` : '') +
        (filters ? `&filter[]=${filters}` : '')

    let newUrlFragment = ""
    if(index in context.matchedGroups){
        newUrlFragment = context.urlFragment.replace(context.matchedGroups[index], contextData);
    }
    else if (context.urlFragment !== ""){
        newUrlFragment = context.urlFragment + `&table${index}{${contextData}}`;
    }
    else {
        newUrlFragment = `table${index}{${contextData}}`;
    }
    return encodeURI('#' + newUrlFragment);
}

function parseUrlFragment(index) {
    const context = getContextFromUrl();
    if(index in context.matchedGroups){
        return context.matchedGroups[index]
            .split('&')
            .map((elem) => elem.split('='))
            .reduce((acc, value) => {
                if (value.length === 2) { // Handle "xxx=yyy"
                    return {...acc, [value[0]]: value[1]}
                } else if (value.length === 3) { // Handle "xxx[]=yyy=zzz"
                    const key = value[0].slice(0, -2);
                    (acc[key] = acc[key] || []).push(`${value[1]}=${value[2]}`);
                    return acc
                } else {
                    return acc;
                }
            }, {});
    }
    return {};
}

function datatableify(table, index) {
    const datatable = $(table);
    const id = datatable.data('id');
    const page_length = 25;
    let page_index = 0;
    let search_history = null;
    let order_history = null;

    const history_state = parseUrlFragment(index);
    if(!jQuery.isEmptyObject(history_state))
    {
        page_index = history_state.page;
        search_history = history_state.search || null;
        if(history_state.order_col && history_state.order_dir){
            order_history = [{
                'column': history_state.order_col,
                'dir': history_state.order_dir
            }]
        }
        if(history_state.filter){
            $(".datatable-filters." + id + " input:checkbox.datatable-filter").each(function () {
                if(history_state.filter.indexOf(this.name) > -1) {
                    $(this).attr('checked', true)
                    let group = $(this).data('group');
                    if(group){
                        $('#'+group).prop('checked', true);
                    }
                }
            })
            $(".datatable-filter-date").each(function () {
                const filter_tag = this
                const element = history_state.filter.find((element) => element.startsWith(filter_tag.name))
                if (element) {
                    $(this).attr('value', element.split('=')[1])
                    $(this).attr('param', element)
                }
            })
        }
    }

    const default_settings = {
        serverSide: true,
        paging: true,
        pageLength: page_length,
        displayStart: page_index * page_length,
        info: true,
        ordering: true,
        searching: true,
        destroy: true,
        columnDefs: [
            { className: "table__cell", targets: "_all" },
            { visible: false, targets: "hidden" },
        ],
        dom: 'rti<"pagination"p>',
        ajax: {
            url: "?format=json",
            data: d => {
                if (search_history !== null){
                    d['search']['value'] = search_history;
                }
                if (order_history !== null){
                    d['order'] = order_history
                    order_history = null;
                }

                var searchstring = $("form:eq(0) :input").val();
                if (searchstring)
                    d["main_search"] = searchstring;
                d["filters"] = [];
                $(".datatable-filter-date").each(function () {
                    // Simple verification to avoid uninitialized or cleared values.
                    const param = $(this).attr('param')
                    if (/.+=.+/.test(param)) {
                        d["filters"].push(param)
                    }
                });
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

                history.replaceState(null, '', buildUrlFragment(index, d))
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

    const date_filter_selector = $('.datatable-filter-date')
    date_filter_selector.each(function() {
        new DateTime($(this), {
            format: 'yyyy-MM-dd HH:mm',
            buttons: { clear: true },
            locale: settings.language.dateTimePickerLocale || 'en',
            i18n: settings.language.dateTimePicker || {}
        });
        $(this).on('change', function(){
            const name = $(this).attr('name')
            const val = $(this).val();
            $(this).attr('param', name + '=' + val)
            table.draw();
        });
    })

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
    if(search_history !== null){
        table.search(search_history)
        search_history = null;
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

    return table;
}

