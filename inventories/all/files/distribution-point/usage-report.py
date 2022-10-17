#!/usr/bin/python3

# cat /etc/apache2/conf-available/charset.conf 
# AddDefaultCharset UTF-8
# SetEnv PYTHONIOENCODING UTF-8
#
# apt install libjs-jquery-tablesorter
# ln -s /usr/share/javascript /var/www/html/javascript

import cgi
import dateutil.parser
import string
import gzip
import os
import sys
import re
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

#import cgitb
#cgitb.enable()

systemapps = ['touch', 'chmod', 'bash', 'gpg-agent', 'Xorg', 'rm', 'xauth', 'dbus-launch',
        'cp', 'sed', 'pulseaudio', 'gvfsd-metadata', 'evolution-source-registry', 'certutil', 'evolution-calendar-factory-subprocess',
        'dconf-service', 'evolution-addressbook-factory-subprocess', 'gnome-keyring-daemon', 'mv', 'mkdir',
        "tracker-miner-fs", "tracker-store", "tracker-miner-apps", "evolution-addressbook-factory", "tracker-extract",
        "evolution-calendar-factory", "polkit-kde-authentication-agent-1", "xdg-desktop-portal-kde",
        "xdg-user-dirs-update"]

import re
def natural_sort(l): 
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(l, key=alphanum_key)

print("Content-type: text/html; charset=utf-8")
print("Cache-Control: no-cache")
print()
header = """
<html><head>
<link type="text/css" rel="stylesheet" href="/javascript/jquery-tablesorter/css/theme.default.css" />
<script type="text/javascript" src="/javascript/jquery/jquery.min.js"></script>
<script type="text/javascript" src="/javascript/jquery-tablesorter/jquery.tablesorter.min.js"></script>
<script type="text/javascript">
    $(function(){ $("#a_h").tablesorter(); });
    $(function(){ $("#a_p").tablesorter(); });
    $(function(){ $("#a_f").tablesorter(); });
    $(function(){ $("#a_s").tablesorter(); });
    $(function(){ $("#a_a").tablesorter(); });
</script>
</head><body>
<div class="container">
"""
print(header)

# ipaddr = cgi.escape(os.environ["REMOTE_ADDR"])

path_var_log = "/var/log"
logs = [path_var_log + "/" + f for f in os.listdir(path_var_log) if f.startswith("network.log")]
logs = list(natural_sort(logs))

interval = 2
shift = 0

for arg in sys.argv:
    if "interval" in arg: interval = int((arg.split("=", 1))[1])
    if "shift" in arg: shift = int((arg.split("=", 1))[1])
args = cgi.FieldStorage()
if "interval" in args:
    interval = int(args["interval"].value)
args = cgi.FieldStorage()
if "shift" in args:
    shift = int(args["shift"].value)

if interval > len(logs): interval = len(logs)
if shift > len(logs)-interval: shift = len(logs)-interval

logs = logs[shift:shift+interval]
logs.reverse()

def print_table(t, id):
    thelist = list(string.ascii_uppercase)
    print("<table id=\"" + id + "\" class=\"tablesorter\"><thead><tr>")
    for (c, h)  in zip(t[0], thelist):
        print("<th>" + h + "</th>")
    print("</tr></thead><tbody>")
    for r in t:
        print("<tr>")
        for c in r:
            print("<td>" + c + "</td>", end = "")
        print("</tr>")
    print("</tbody></table>")

a_h, a_p, a_f, a_s, a_a = [], [], [], [], []
d_f = {}
records_dates, ip_addresses = [], []
usernames, apps = {}, {}
apps_count = 0
changed_count = {}
failed_count = {}

xdata, ydata, ydata_second, ydata_third, ydata_fourth = [], [], [], [], []
yapps = {}
ts = "value=0000-00-00"

with open('/var/log/usage-report.log', "r") as f:
    for line in f:
        if "input type='hidden'" in line:
            a = line.split()
            v = re.findall("\d+", a[4])[0]
            if "log_timestamp" in line:
                a_h.append([])
                ts = a[4].strip('>')
                a_h[-1].append(ts)
            if "unique_addresses" in line:
                a_h[-1].append("unique_addresses=" + v)
                ydata.append(int(v))
            if "unique_usernames" in line:
                a_h[-1].append("unique_usernames=" + v)
                ydata_second.append(int(v))
            if "changed_count"    in line:
                a_h[-1].append("changed_count=" + v)
                ydata_third.append(int(v))
            if "failed_count"     in line:
                a_h[-1].append("failed_count=" + v)
                ydata_fourth.append(int(v))
            if "apps_count"       in line: a_h[-1].append("apps_count=" + v)
        if '[(' in line and ')]' in line:
            appstring = re.findall("\[\(.*\)\]", line)
            applist = json.loads(appstring[0].replace("(", "[").replace(")", "]").replace("\'", "\""))
            if ts not in yapps.keys(): yapps[ts] = []
            yapps[ts].append(applist)
xdata = [i for i in range(-len(ydata)+1, 1)]
plt.plot(xdata, ydata, label = "Unique addresses", color="blue")
plt.plot(xdata, ydata_second, label = "Unique usernames", color="green")
plt.plot(xdata, ydata_third, label = "Changed count", color="yellow")
plt.plot(xdata, ydata_fourth, label = "Failed count", color="red")
plt.title("Records")
plt.xlabel("Day")
plt.legend(loc="upper left")
plt.savefig("/var/www/html/files/usage-report.png")
plt.close()
yappsplot = {}
for key in yapps.keys():
    for host in yapps[key]:
        for app in host:
            yappsplot[app[0]] = []
for key in sorted(yapps.keys()):
    for x in sorted(yappsplot.keys()): yappsplot[x].append(0)
    for hosts in yapps[key]:
        for app in hosts:
            yappsplot[app[0]][-1] += 1
for key in yappsplot.keys():
    if max(yappsplot[key]) < 5: systemapps.append(key)
for key in systemapps:
    if key in yappsplot.keys(): yappsplot.pop(key)
xdata = [i for i in range(-len(list(yappsplot.values())[0])+1, 1)]
for key in list(yappsplot.keys()):
    plt.plot(xdata, yappsplot[key], label = key)
plt.title("Hosts with apps")
plt.xlabel("Day")
plt.legend(loc="upper left")
plt.savefig("/var/www/html/files/usage-report-apps.png")
plt.close()

for log in logs:
    try:
        if ".gz" in log:
            f = gzip.open(log, 'rt', encoding = "ascii", errors = "ignore")
        else:
            f = open(log, 'r', encoding = "ascii", errors = "ignore")
    except IOError:
        continue
    for line in f:
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
            a[1] = "\"" + a[1] + "\""
            a_p.append(a)
            ip_addresses.append(a[1])
            records_dates.append(a[0])
        if 'basic_ansible_facts' in line:
            if 'ansible_product_serial' in line:
                try:
                    ansible_product_serial = re.findall("ansible_product_serial=.*", line)[0]
                    ansible_product_serial = ansible_product_serial.replace("ansible_product_serial=", "")
                    line = re.sub("ansible_product_serial=.*", "", line)
                except:
                  ansible_product_serial = "none"  
            else: ansible_product_serial = "none"
            if 'macaddress' in line:
                macaddress = re.findall("macaddress=[a-zA-Z0-9:-]*", line)[0]
                macaddress = macaddress.replace("macaddress=", "")
                line = re.sub("macaddress=[a-zA-Z0-9:-]*", "", line)
            else: macaddress = "none"
            if 'var_site_address' in line:
                siteaddress = re.findall("var_site_address=[a-z0-9_-]*", line)[0]
                siteaddress = siteaddress.replace("var_site_address=", "")
                line = re.sub("var_site_address=[a-z0-9_-]*", "", line)
            else: siteaddress = "default"
            a = line.split()
            if (len(a) < 14): continue
            if 'basic_ansible_facts' not in a[5]: continue
            a[2] = str(dateutil.parser.parse(a[0] + " " + a[1] + " " + a[2]))
            a = a[2:4] + a[8:]
            a[8:] = [' '.join(a[8:])]
            a[1] = "\"" + a[1] + "\""
            a.append(siteaddress)
            a.append(macaddress)
            a.append(ansible_product_serial)
            # a_f.append(a)
            d_f[(a[1], a[3])] = a
        if 'authentication success' in line:
            a = line.split()
            if (len(a) < 15): continue
            a[2] = str(dateutil.parser.parse(a[0] + " " + a[1] + " " + a[2]))
            try: a.remove("fly-dm:")
            except ValueError: pass
            if 'authentication' not in a[6]: continue
            a = a[2:4] + a[14:15] + a[9:10]
            a[1] = "\"" + a[1] + "\""
            a_s.append(a)
            if a[3] == "uid=0": a[3] = a[2]
            else:
                if a[2].lower() not in usernames.values(): usernames[a[3].lower()] = a[2].lower()
        if 'type=SYSCALL' in line:
            if "ThreadPoolForeg" in line: continue
            if not "audit_home" in line: continue
            a = line.split()
            if (len(a) < 33): continue
            uid = a[20].strip("a")
            app = a[31]
            if not "\"" in app: continue
            app = (app.rsplit('/', 1))[1] if '/' in app else (app.rsplit('=', 1))[1]
            app = app.strip("\"")
            if uid in apps:
                if app in apps[uid]:
                    apps[uid][app] += 1
                    apps_count += 1
                else:
                    apps[uid][app] = 1
            else:
                apps[uid] = {app: 1}
 
for key in apps:
    d = apps[key]
    s = sorted(d.items(), key = lambda x: x[1])
    username = usernames[key] if key in usernames.keys() else " "
    a_a.append([key, username, str(s)])

a_f = list(d_f.values())

print("<a href='#h_u_r'>Unique records</a>")
print("<a href='#h_a_h'>History</a>")
print("<a href='#h_a_p'>Ansible play</a>")
print("<a href='#h_a_f'>Basic ansible facts</a>")
print("<a href='#h_a_s'>Authentication success</a>")
print("<a href='#h_a_a'>Application analysis</a>")

print("<h1 id='h_u_r'>Unique records (" + str(min(records_dates)) + " - " + str(max(records_dates)) + ")</h1>")
print("<h2>IP addresses: " + str(len(set(ip_addresses))) + "</h2>")
print("<h2>Usernames: " + str(len(usernames)) + "</h2>")

print("<img src='/files/usage-report.png'>") 
print("<img src='/files/usage-report-apps.png'>") 

print("<br />")
print("<h1 id='h_a_h'>History</h1>")
print_table(a_h, "a_h")

print("<br />")
print("<h1 id='h_a_p'>Ansible play</h1>")
print_table(a_p, "a_p")

print("<br />")
print("<h1 id='h_a_f'>Basic ansible facts</h1>")
print_table(a_f, "a_f")

print("<br />")
print("<h1 id='h_a_s'>Authentication success</h1>")
print_table(a_s, "a_s")

print("<br />")
print("<h1 id='h_a_a'>Application analysis</h1>")
print_table(a_a, "a_a")

print("<input type='hidden' id='log_timestamp' name='log_timestamp' value='" + str(max(records_dates)) + "'>")
print("<input type='hidden' id='unique_addresses' name='unique_addresses' value='" + str(len(set(ip_addresses))) + "'>")
print("<input type='hidden' id='unique_usernames' name='unique_usernames' value='" + str(len(usernames)) + "'>")
print("<input type='hidden' id='changed_count' name='changed_count' value='" + str(sum(changed_count.values())) + "'>")
print("<input type='hidden' id='failed_count' name='failed_count' value='" + str(sum(failed_count.values())) + "'>")
print("<input type='hidden' id='apps_count' name='apps_count' value='" + str(apps_count) + "'>")

print('</div></body></html>')
