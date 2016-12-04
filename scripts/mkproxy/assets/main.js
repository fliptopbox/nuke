(function($){
    String.prototype.hashCode = function() {
        var hash = 0, i, chr, len;
        if (this.length === 0) return hash;
        for (i = 0, len = this.length; i < len; i++) {
            chr   = this.charCodeAt(i);
            hash  = ((hash << 5) - hash) + chr;
            hash |= 0; // Convert to 32bit integer
        }
        return hash;
    };
    var main = $('#main'),
        progress = $('#progress'),
        workers = $('#workers'),
        log = $('#log'),
        work_dct = {},
        log_filename = null,
        log_template = '<span class=":CLASSNAME:" title=":ALT:">:TEXT:</span>',
        view = function(html) {
            main.html(html)
        },
        get_work_rate = function (obj) {
            var html = []
            $.each(obj, function (name, value) {
                //console.log(name, value)
                html.push('<div class="work_row"><b>'+ name +'</b><i>'+ value +'</i></div>')
            })
            return html.join('')
        },
        get_time_fmt = function (milliseconds, limit) {
            if(/^[0-9]+\.[0-9]+$/.test(String(milliseconds))) {
                milliseconds *= 1000; // python might use seconds
            }
            var i = 0;
            var ms = milliseconds;
            var fmt = ['sec', 'min', 'hr', 'day', 'week', 'month', 'year', 'decade', 'cemtury'];
            var mod = [1000, 60, 60, 24, 7, 4, 12, 10, 100, 1];
            var plural = null;

            for(i; i < fmt.length-1; i++) {
                ms /= mod[i];
                if (limit && limit === fmt[i]) { break; }
                if (parseInt(ms/mod[i+1], 10) == 0) { break; }
            }

            plural = (ms > 1 ? 's' : '');
            return [
                String(i > 2 ? ms.toFixed(2) : parseInt(ms, 10)).replace(/\.[0]+$/, ''),
                fmt[i] + plural
            ].join(' ');

        },
        get_node_status = function (name, value) {
            var array = value.split('@');
            var ip = array[0];
            var ts = array[1];
            var diff = 0
            if (!/^[0-9]+$/.test(ts)) { return value; }
            ts = parseInt(ts, 10) * 1000
            diff = (parseInt(new Date().valueOf(), 10) - ts)/1000;
            classname = diff < (5*60*1000) ? 'good' :
                        diff < (15*60*1000) ? 'medium' :  
                        diff < (30*60*1000) ? 'slow' :  
                        diff < (60*60*1000) ? 'warning' :
                        'inactive';

            return value + ' <em class="status status-' + classname + '">' + get_time_fmt(diff) + '</em>';
        },
        tsv_to_html = function (row) {
            if (!row.trim()) { return ''; }
            row = row.trim().split('\t')
            if (row.length < 4) { return ''; }

            var diff
            var work_id = row[1].toLowerCase().trim()
            var work_type = (row[2].match(/^(finish|start)/i) || [''])[0].toLowerCase()

            var classnames = [
                row[0].toLowerCase().trim(),
                row[1].toLowerCase().trim(),
                work_type,
            ].join(' ')

            if (work_type && /^finish/i.test(work_type)) {
                work_dct = work_dct || {}
                work_dct[work_id] = work_dct[work_id] || 0
                work_dct[work_id] += 1
            }

            row[0] = log_template.replace(':TEXT:', row[0]).replace(':CLASSNAME:', 'log-cell log-type').replace(':ALT:', '')
            row[1] = log_template.replace(':TEXT:', row[1]).replace(':CLASSNAME:', 'log-cell log-worker').replace(':ALT:', '')
            row[2] = log_template.replace(':TEXT:', row[2]).replace(':CLASSNAME:', 'log-cell log-desc').replace(':ALT:', '')
            row[3] = log_template.replace(':TEXT:', row[3].split(/[\/\\]/).slice(-1).join('/')).replace(':CLASSNAME:', 'log-cell log-value').replace(':ALT:', row[3])
            row[4] = log_template.replace(':TEXT:', row[4] || '').replace(':CLASSNAME:', 'log-cell log-extra').replace(':ALT:', '')
            row[5] = log_template.replace(':TEXT:', row[5] && row[5].split(' ')[1] || '').replace(':CLASSNAME:', 'log-cell log-time').replace(':ALT:', row[5])

            return '<div class="log-row ' + classnames + '">' + row.join('') + '</div>'

        },
        get_log = null,
        get_log_file = function () {
            var array = null,
                partial,
                html = '',
                parse = function () {
                    $.get(log_filename, function (txt) {
                        array = txt.split('\n')
                        var n = array.length - 1,
                            row;

                        while (n) {
                            row = array[n].trim() || '';
                            if (row) {
                                html += tsv_to_html(row)
                            }
                            n -= 1
                        }

                        log.html(html)
                        workers.html(get_work_rate(work_dct));
                        work_dct = null;
                    })
                };
            return setTimeout(parse, 0);
        },
        get_config_row = function (name, value) {
            var is_node_worker = /^node/i.test(name)
            value = String(value || '').trim()
            value = is_node_worker ? get_node_status(name, value) : value.trim()
            return [
                '<div class="row">',
                    '<div class="col name">',
                        name,
                    '</div>',
                    '<div class="col value">',
                        value,
                    '</div>',
                '</div>'
            ].join('\n');
        },
        date_string = function (d) {
            d = !d ? new Date() : new Date(d)
            d = d.toString().split(' ').slice(0,5)
            return d.join(' ')
        },
        now = function () {
            return new Date().valueOf();
        },
        config_dates = {},
        poll_previous = null,
        poll_server = function () {
            $.getJSON('config.json', function(d){
                //console.log(d);
                var text = [],
                    percent = 0,
                    keys = [],
                    hash = (JSON.stringify(d)).hashCode();

                if (hash === poll_previous) {
                    console.log("Nothing to do ...");
                    return;
                }
                poll_previous = hash;

                if (get_log) { get_log_file(); }


                $(d).each(function(key, obj){
                    log_filename = log_filename || obj.log_filename;
                    obj['date_now'] = date_string()
                    $.each(obj, function (name, value) {
                        // console.log(name, value)
                        percent = (obj.total_progress / obj.total_files) * 100

                        if (/^date/i.test(name)) {
                            obj[name] = date_string(value)
                            config_dates[name] = parseInt(new Date(value).valueOf(), 10);
                        }
                        if (!/^dst|src|work/i.test(name)) {
                            keys.push(name)
                        }
                    });

                    $.each(keys.sort(), function (i, val) {
                        text.push(get_config_row(val, obj[val]))
                    })


                    // text.push(get_config_row('now', now()))
                    // console.clear()
                    console.log(now())
                })
                progress.html('<div class="bar" style="width:' + percent + '%"><em>' + parseInt(percent,10) + '%</em></div>')
                view(text.join('\n'))
            });
        };
    poll_server();
    setInterval(poll_server, 15000);

    var logContainer = $('#log-container');
    $('#load_log').on('click', function (e) {
        e.preventDefault();
        logContainer.toggleClass('show-log');
        get_log = logContainer.hasClass('show-log') // global switch
        if (!get_log) {
            // hide and empty contents
            log.html('Loading ....');
            $(this).html('View log file');
            return;
        }

        $(this).html('Hide log file');
        return get_log_file();

    });
}(Zepto))