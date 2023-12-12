#!/usr/bin/python3

# cat /etc/apache2/conf-available/charset.conf
# AddDefaultCharset UTF-8
# SetEnv PYTHONIOENCODING UTF-8

#
# 30 23 * * * root /bin/bash -c '/usr/lib/cgi-bin/secure/usage-report.py cache=false format=xml report=all cgienv=false > \
# /var/log/usage-report/usage-report-$(date -d "today" +"\%Y-\%m-\%d-\%H\%M").xml; \
# chown www-data /var/log/usage-report/usage-report-$(date -d "today" +"\%Y-\%m-\%d-")*.xml'
#

import datetime, cgi, dateutil.parser, string, gzip, os, pwd, sys, re, json, xmltodict, matplotlib
import glob, collections, time
import matplotlib.pyplot as plt
from lxml import html

matplotlib.use("Agg")

# paths
path_var_log = "/var/log"
path_history_dir = "/var/log/usage-report"
tmp_filename = "usage-report-tmp.xml"
tmp_history_filename = "usage-report-history.json"
log_startswith = "network.log"
web_images_dir = "/var/www/html/files"
web_images_dir_rel = "/files" # relative
web_user = "www-data"

# a, f, p, e, s, h
auth_success_header = ["timestamp", "ip", "user", "uid"]
basic_ansible_facts_header = ["timestamp", "ip", "host_time", "hostname", "kernel", "root_dev", "free_space", "ntfs_part",
    "uptime", "logged_on_users", "site", "mac", "serial", "company", "geo_coord", "ou", "users_apps"]
ansible_play_header = ["timestamp", "ip", "ok", "changed", "unreachable", "failed"]
ansible_exec_header = ["timestamp", "ip", "role", "task", "status", "tag"]
basic_security_facts_header = ["timestamp", "ip", "ma", "mcs", "mls", "ima", "dlp_aux", "av_aux", "host_flags"]
history_header = ["date", "unique_addresses", "unique_users", "changed_count", "failed_count"]
ansible_facts_packages = ["timestamp", "ip", "pkg", "version"]

def natural_sort(l):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(l, key=alphanum_key)

def print_xml(header, t, name, ts, rec_name):
    if len(t) == 0: return
    print(f"<{name} timestamp='{ts}'>")
    for r in t:
        print(f"<{rec_name}>", end = "")
        for h, c in zip(header, r):
            print(f"<{h}>{c}</{h}>", end = "")
        print(f"</{rec_name}>")
    print(f"</{name}>")

def print_html_header():
    print("Content-type: text/html; charset=utf-8")
    print("Cache-control: no-cache")
    print()
    header = """
    <html><head>
    <link type="text/css" rel="stylesheet" href="/javascript/jquery-tablesorter/css/theme.default.css" />
    <script type="text/javascript" src="/javascript/jquery/jquery.min.js"></script>
    <script type="text/javascript" src="/javascript/jquery-tablesorter/jquery.tablesorter.min.js"></script>
    <script type="text/javascript">
        $(function(){ $("#a_p").tablesorter(); });
        $(function(){ $("#a_f").tablesorter(); });
        $(function(){ $("#a_a").tablesorter(); });
        $(function(){ $("#a_e").tablesorter(); });
        $(function(){ $("#a_s").tablesorter(); });
    </script>
    </head><body>
    <div class="container">
    """
    print(header)

def print_xml_header():
    print("Content-type: text/xml; charset=utf-8")
    print("Cache-control: max-age=900")
    print()

def print_json_header():
    print("Content-type: application/json")
    print("Cache-control: max-age=900")
    print()

def print_html_table(header, t, id):
    if len(t) == 0: return
    print(f"<table id='{id}' class='tablesorter'><thead><tr>")
    for (c, h)  in zip(t[0], header):
        print(f"<th>{h}</th>")
    print("</tr></thead><tbody>")
    for r in t:
        print("<tr>")
        for c in r:
            print(f"<td>{str(c)}</td>", end = "")
        print("</tr>")
    print("</tbody></table>")

def analize_logs(log_startswith, interval, shift, cache):
    fname_tmp = path_history_dir + "/" + tmp_filename
    if cache and os.path.exists(fname_tmp) and (time.time() - os.path.getmtime(fname_tmp) < 15*60):
        return

    logs = [path_var_log + "/" + f for f in os.listdir(path_var_log) if f.startswith(log_startswith)]
    logs = list(natural_sort(logs))

    if interval > len(logs): interval = len(logs)
    if shift > len(logs)-interval: shift = len(logs)-interval

    logs = logs[shift:shift+interval]
    logs.reverse()

    a_a, a_f, a_p, a_e, a_s, a_g = [], [], [], [], [], []

    changed_count, failed_count, usernames, pkgs = {}, {}, {}, {}

    for log in logs:
        try:
            if ".gz" in log:
                f = gzip.open(log, 'rt', encoding = "ascii", errors = "ignore")
            else:
                f = open(log, 'r', encoding = "ascii", errors = "ignore")
        except IOError:
            continue
        prevline = ""
        for line in f:
            try:
                if 'basic_ansible_facts:' in line:
                    jsonstr = line.split("basic_ansible_facts:", 1)[1] \
                        .replace("\'", "\"").replace(": True", ": true").replace(": False", ": false")
                    d = json.loads(jsonstr)
                    a = line.split()
                    a[2] = str(dateutil.parser.parse(a[0] + " " + a[1] + " " + a[2]))
                    a = a[2:3] + [d.get(k, "N/A") for k in basic_ansible_facts_header[1:]]
                    a_f.append(a)

                if "ansible_facts.packages:" in line:
                    jsonstr = line.split("ansible_facts.packages:", 1)[1] \
                        .replace("\'", "\"").replace(": True", ": true").replace(": False", ": false")
                    d = json.loads(jsonstr)
                    a = line.split()
                    a[2] = str(dateutil.parser.parse(a[0] + " " + a[1] + " " + a[2]))
                    for k in d.keys(): pkgs[(a[3], k)] = [a[2], a[3], d[k]["name"], d[k]["version"]]

                if 'basic_security_facts:' in line:
                    jsonstr = line.split("basic_security_facts:", 1)[1] \
                        .replace("\'", "\"").replace(": True", ": true").replace(": False", ": false")
                    d = json.loads(jsonstr)
                    a = line.split()
                    a[2] = str(dateutil.parser.parse(a[0] + " " + a[1] + " " + a[2]))
                    a = a[2:4] + [d.get(k, "N/A") for k in basic_security_facts_header[2:]]
                    a_s.append(a)

                if 'changed=' in line:
                    a = line.split()
                    if (len(a) < 11): continue
                    if 'changed=' not in a[8]: continue
                    changed_count.setdefault(a[3],0)
                    changed_count[a[3]] = 1 if int((a[8].split("=", 1))[1]) > 0 else 0
                    failed_count.setdefault(a[3],0)
                    failed_count[a[3]] = int((a[10].split("=", 1))[1])
                    a[2] = str(dateutil.parser.parse(a[0] + " " + a[1] + " " + a[2]))
                    a = a[2:4] + a[7:]
                    a = list(map(lambda x: x if "=" not in x else (x.split("="))[1], a))
                    a_p.append(a)

                if 'authentication success' in line:
                    a = line.split()
                    if (len(a) < 15): continue
                    a[2] = str(dateutil.parser.parse(a[0] + " " + a[1] + " " + a[2]))
                    try: a.remove("fly-dm:")
                    except ValueError: pass
                    if 'authentication' not in a[6]: continue
                    a = a[2:4] + a[14:15] + a[9:10]
                    a = list(map(lambda x: x if "=" not in x else (x.split("="))[1], a))
                    a_a.append(a)
                    if a[3] == "uid=0": a[3] = a[2]
                    elif a[2].lower() not in usernames.values(): usernames[a[3].lower()] = a[2].lower()

                if "TASK [" in prevline:
                    a = line.split()
                    a[2] = str(dateutil.parser.parse(a[0] + " " + a[1] + " " + a[2]))
                    role_and_task = re.search("\[(.*)\]", prevline).group(1).split(":")
                    if len(role_and_task) > 1:
                        task = role_and_task[1].strip()
                        if "@" in task:
                            tag = task.split("@")[1]
                            task = task.split("@")[0]
                        else:
                            tag = ""
                        a_e.append([a[2], a[3], role_and_task[0].strip(), task,
                            "changed" if ("failed: [" not in line) else "failed", tag])
            except: pass
            prevline = line # todo: store with ip
    ts = datetime.datetime.now().isoformat()
    for x in pkgs.values(): a_g.append(x)
    original_stdout = sys.stdout
    fname = path_history_dir + "/" + tmp_filename
    if os.path.exists(fname): os.remove(fname)
    with open(fname, "a") as f:
        sys.stdout = f
        print(f"<usage_report date='{ts}'>")
        print_xml(basic_ansible_facts_header, a_f, "basic_ansible_facts", ts, "rec_basic")
        print_xml(ansible_play_header, a_p, "ansible_play", ts, "rec_play")
        print_xml(auth_success_header, a_a, "auth_success", ts, "rec_auth")
        print_xml(ansible_exec_header, a_e, "ansible_exec", ts, "rec_exec")
        print_xml(basic_security_facts_header, a_s, "basic_security_facts", ts, "rec_sec")
        print_xml(ansible_facts_packages, a_g, "ansible_facts_packages", ts, "rec_pkg")
        print("</usage_report>")
        uid = pwd.getpwnam(web_user).pw_uid
        gid = os.stat(fname).st_gid
        os.chown(fname, uid, gid)
        sys.stdout = original_stdout

def read_history():
    fname_hist = path_history_dir + "/" + tmp_history_filename
    if os.path.exists(fname_hist):
        with open(fname_hist) as f:
            d = json.load(f)
        return d['users'], d['computers'], d['history']

def write_history():
    fname_hist = path_history_dir + "/" + tmp_history_filename
    u_d, c_d, h_d = {}, {}, {}
    users, computers, history = [], [], []
    for fname in sorted(glob.glob(path_history_dir + '/usage-report-[0-9]*.xml')):
        if os.stat(fname).st_size == 0: continue
        with open(fname, 'r') as f:
            try:
                d = xmltodict.parse(f.read())
                daily = { 'users': set(), 'computers': set(), 'changed': set(), 'failed': set() }
                if 'auth_success' in d['usage_report']:
                    for e in d['usage_report']['auth_success']['rec_auth']:
                        u_d[(e['user'])] = e
                        daily['users'].add(e['user'])
                if 'basic_ansible_facts' in d['usage_report']:
                    for e in d['usage_report']['basic_ansible_facts']['rec_basic']:
                        c_d[e['mac']] = e
                        daily['computers'].add(e['mac'])
                if 'ansible_play' in d['usage_report']:
                    for e in d['usage_report']['ansible_play']['rec_play']:
                        if int(e['changed']) > 0: daily['changed'].add(e['ip'])
                        if int(e['failed']) > 0: daily['failed'].add(e['ip'])
                h_d[d['usage_report']['@date']] = { 'date': d['usage_report']['@date'],
                    'users': len(daily['users']), 'computers': len(daily['computers']),
                    'changed': len(daily['changed']), 'failed': len(daily['failed']) }
            except: pass
    u_d = dict(sorted(u_d.items(), key=lambda x: x[1]['timestamp'], reverse=True))
    c_d = dict(sorted(c_d.items(), key=lambda x: x[1]['timestamp'], reverse=True))
    last_by_ip = {}
    for c in c_d: last_by_ip[c_d[c]['ip']] = {'user': 'N/A', 'auth': 'N/A'}
    for u in u_d: last_by_ip[u_d[u]['ip']] = {'user': u, 'auth': u_d[u]['timestamp']}
    for i, x in enumerate(u_d.values()):
        x.update({'id': i})
        x.move_to_end('id', last=False)
        users.append(x)
    for i, x in enumerate(c_d.values()):
        x.update({'id': i})
        x.move_to_end('id', last=False)
        x.pop('kernel', None)
        x.pop('root_dev', None)
        x.pop('free_space', None)
        x.pop('ntfs_part', None)
        x.pop('uptime', None)
        x.pop('logged_on_users', None)
        x.pop('host_time', None)
        x.update({'user': last_by_ip[x['ip']]['user']})
        x.update({'auth': last_by_ip[x['ip']]['auth']})
        computers.append(x)
    for x in h_d.values(): history.append(x)
    with open(fname_hist, "w") as f:
        json.dump({'users': users, 'computers': computers, 'history': history}, f)
    uid = pwd.getpwnam(web_user).pw_uid
    gid = os.stat(fname_hist).st_gid
    os.chown(fname_hist, uid, gid)
    return users, computers, history

def plot_history(history):
    xdata = []
    ydata = collections.defaultdict(list)
    for i, rec in zip(range(-len(history)+1, 1), history):
        xdata.append(i)
        for k in rec:
            ydata[k].append(rec[k])
    plt.rcParams['figure.figsize'] = [10.0, 5.0]
    plt.rcParams['figure.dpi'] = 125
    plt.plot(xdata, ydata['computers'], label = "Unique addresses", color="blue")
    plt.plot(xdata, ydata['users'], label = "Unique usernames", color="green")
    plt.plot(xdata, ydata['changed'], label = "Changed count", color="yellow")
    plt.plot(xdata, ydata['failed'], label = "Failed count", color="red")
    plt.title("Records")
    plt.xlabel("Day")
    plt.legend(loc="upper left")
    plt.savefig(web_images_dir + "/usage-report.png")
    plt.close()

def read_daily_xml(shift = 0):
    fname = path_history_dir + "/" + tmp_filename
    if shift > 0 or not os.path.exists(fname):
        dt = datetime.datetime.now() - datetime.timedelta(shift)
        ts_date = dt.isoformat()
        ts_date = re.search("\d{4}-[01]\d-[0-3]\d", ts_date)[0]
        fname = sorted(glob.glob(path_history_dir + "/usage-report-" + ts_date + "-*.xml"))[-1]
    with open(fname, 'r') as f:
        r = xmltodict.parse(f.read())
    return r

def od_to_list(od):
    keys, rows = [], []
    for sub_dict in od:
        row = []
        for key in sub_dict:
            if key not in keys:
                keys.append(key)
            row.append(sub_dict[key])
        rows.append(row)
    return keys, rows

def main():
    # read cli and cgi args
    format = "html"
    report = "default"
    interval = 1    # read last one day
    shift = 0       # from now
    cache = True
    cgienv = True
    rehistory = False
    for arg in sys.argv[1:]:
        if "format" in arg:     format = arg.split("=", 1)[1]
        if "report" in arg:     report = arg.split("=", 1)[1]
        if "interval" in arg:   interval = int((arg.split("=", 1))[1])
        if "shift" in arg:      shift = int((arg.split("=", 1))[1])
        if "cache" in arg:      cache = True if arg.split("=", 1)[1].lower() == "true" else False
        if "cgienv" in arg:     cgienv = False if arg.split("=", 1)[1].lower() == "false" else True
        if "rehistory" in arg:  rehistory = False if arg.split("=", 1)[1].lower() == "false" else True
    args = cgi.FieldStorage()
    if "format" in args:    format = args["format"].value
    if "report" in args:    report = args["report"].value
    if "interval" in args:  interval = int(args["interval"].value)
    if "shift" in args:     shift = int(args["shift"].value)
    if "cache" in args:     cache = True if args["cache"].value.lower() == "true" else False
    if "cgienv" in args:    cgienv = False if args["cgienv"].value.lower() == "false" else True
    if "rehistory" in args: rehistory = False if args["rehistory"].value.lower() == "false" else True

    if "secure" not in os.path.abspath(__file__):
        report = "last"

    ts = datetime.datetime.now().isoformat()

    analize_logs(log_startswith, interval, shift, cache)
    d = read_daily_xml(shift)

    users, computers, history = read_history() if not rehistory else write_history()
    plot_history(history)

    if format == "html":
        print_html_header()
        if report == "history":
            print("<a href='#h_a_s'>Last basic ansible facts</a>")
            print("<br />")
            print("<h1 id='h_a_s'>Last basic ansible facts</h1>")
            print_html_table(*od_to_list(history), "a_s")
        if report == "last":
            print("<a href='#h_a_f'>Last basic ansible facts</a>")
            print("<a href='#h_a_a'>Last authentication success</a>")
            print("<br />")
            print("<br />")
            print(f"<img src='{web_images_dir_rel}/usage-report.png'>")
            print("<h1 id='h_a_f'>Last basic ansible facts</h1>")
            print_html_table(*od_to_list(computers), "a_f")
            print("<br />")
            print("<h1 id='h_a_a'>Last authentication success</h1>")
            print_html_table(*od_to_list(users), "a_a")
        if report == "default":
            print("<a href='#h_a_p'>Ansible play</a>")
            print("<a href='#h_a_f'>Basic ansible facts</a>")
            print("<a href='#h_a_a'>Authentication success</a>")
            print("<a href='#h_a_e'>Ansible exec</a>")
            print("<a href='#h_a_s'>Basic security facts</a>")
            print("<br />")
            print(f"<img src='{web_images_dir_rel}/usage-report.png'>")
            print("<br />")
            print("<h1 id='h_a_p'>Ansible play</h1>")
            if 'ansible_play' in d['usage_report']:
                print_html_table(*od_to_list(d['usage_report']['ansible_play']['rec_play']), "a_p")
            print("<br />")
            print("<h1 id='h_a_f'>Basic ansible facts</h1>")
            if 'basic_ansible_facts' in d['usage_report']:
                print_html_table(*od_to_list(d['usage_report']['basic_ansible_facts']['rec_basic']), "a_f")
            print("<br />")
            print("<h1 id='h_a_a'>Authentication success</h1>")
            if 'auth_success' in d['usage_report']:
                print_html_table(*od_to_list(d['usage_report']['auth_success']['rec_auth']), "a_a")
            print("<br />")
            print("<h1 id='h_a_e'>Ansible exec</h1>")
            print("<p>Only in json and xml formats</p>")
            # if 'ansible_exec' in d['usage_report']:
            #     print_html_table(*od_to_list(d['usage_report']['ansible_exec']['rec_exec']), "a_e")
            print("<br />")
            print("<h1 id='h_a_s'>Basic security facts</h1>")
            if 'basic_security_facts' in d['usage_report']:
                print_html_table(*od_to_list(d['usage_report']['basic_security_facts']['rec_sec']), "a_s")
        print('</div></body></html>')
    if format == "xml":
        if cgienv: print_xml_header()
        print(f"<usage_report date='{d['usage_report']['@date']}'>")
        if report == "history":
            print_xml(*od_to_list(history), "history", ts, "rec_history")
        if report == "last":
            print_xml(*od_to_list(computers), "last_computers", ts, "rec_comp")
            print_xml(*od_to_list(users), "last_users", ts, "rec_user")
        if report == "basic" or report == "all":
            print_xml(*od_to_list(d['usage_report']['basic_ansible_facts']['rec_basic']), "basic_ansible_facts",
                d['usage_report']['basic_ansible_facts']["@timestamp"], "rec_basic")
        if report == "play" or report == "all":
            print_xml(*od_to_list(d['usage_report']['ansible_play']['rec_play']), "ansible_play",
                d['usage_report']['ansible_play']["@timestamp"], "rec_play")
        if report == "auth" or report == "all":
            print_xml(*od_to_list(d['usage_report']['auth_success']['rec_auth']), "auth_success",
                d['usage_report']['auth_success']["@timestamp"], "rec_auth")
        if report == "exec" or report == "all":
            print_xml(*od_to_list(d['usage_report']['ansible_exec']['rec_exec']), "ansible_exec",
                d['usage_report']['ansible_exec']["@timestamp"], "rec_exec")
        if report == "sec" or report == "all":
            print_xml(*od_to_list(d['usage_report']['basic_security_facts']['rec_sec']), "basic_security_facts",
                d['usage_report']['basic_security_facts']["@timestamp"], "rec_sec")
        if report == "pkgs" or report == "all":
            print_xml(*od_to_list(d['usage_report']['ansible_facts_packages']['rec_pkg']), "ansible_facts_packages",
                d['usage_report']['ansible_facts_packages']["@timestamp"], "rec_pkg")
        print("</usage_report>")
    if format == "json":
        if cgienv: print_json_header()

        if   report == "all":     print(json.dumps(d))
        elif report == "history": print(json.dumps(history))
        elif report == "last":    print(json.dumps({"last_computers": computers, "last_users": users}))
        elif report == "basic":   print(json.dumps(d['usage_report']['basic_ansible_facts']))
        elif report == "play":    print(json.dumps(d['usage_report']['ansible_play']))
        elif report == "auth":    print(json.dumps(d['usage_report']['auth_success']))
        elif report == "exec":    print(json.dumps(d['usage_report']['ansible_exec']))
        elif report == "sec":     print(json.dumps(d['usage_report']['basic_security_facts']))
        elif report == "pkgs":    print(json.dumps(d['usage_report']['ansible_facts_packages']))

if __name__ == "__main__":
    main()
