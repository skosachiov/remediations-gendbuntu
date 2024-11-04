#!/usr/bin/python3

# kinit -kt /etc/krb5.keytab SERVER\$@REALM
# ldapsearch -H ldap://dc.example.com -o ldif-wrap=no -E pr=2147483647/noprompt -b "DC=example,DC=com" "(&(objectClass=computer))" > /tmp/msad.ldif
#
# ./msad-parsing.py /tmp/msad.ldif /var/log/usage-report/usage-report-history.json /tmp/msad-report.xml
#

LAG_ANSIBLE = 45
LAG_MSAD = 14
DEBUG = False

import sys, base64, uuid, struct, datetime, xmltodict, json
from dateutil import parser

ldif = [{}]
clear = set()
unclear = set()
parser_err_count = 0

def convert_sid(binary):
    version = struct.unpack('B', binary[0:1])[0]
    assert version == 1, version
    length = struct.unpack('B', binary[1:2])[0]
    authority = struct.unpack(b'>Q', b'\x00\x00' + binary[2:8])[0]
    string = 'S-%d-%d' % (version, authority)
    binary = binary[8:]
    assert len(binary) == 4 * length
    for i in range(length):
        value = struct.unpack('<L', binary[4*i:4*(i+1)])[0]
        string += '-%d' % value
    return string

def convert_nt_time(nt_time):
   ts = int((int(nt_time) / 10000000) - 11644473600)
   return datetime.datetime.fromtimestamp(ts).isoformat()

with open(sys.argv[1], "r") as f:
    for line in f:
        line = line.strip()
        if line == '':
            ldif.append({})
            continue
        if line[0] == '#':
            continue
        parts = line.split()
        key = parts[0][:-1]
        val = ' '.join(parts[1:])
        if key[-1] == ':':
            key = key[:-1]
            if key == 'userCertificate': continue
            try:
                val = base64.b64decode(val).decode('utf-8')
                clear.add(key)
            except:
                try:
                    val = str(uuid.UUID(bytes_le=base64.b64decode(val)))
                    clear.add(key)
                except:
                    try:
                        val = convert_sid(base64.b64decode(val))
                        clear.add(key)
                    except:
                        if DEBUG: print('skip:', key, val, file = sys.stderr)
                        unclear.add(key)
        else:
            if key in ['lastLogon', 'lastLogonTimestamp', 'pwdLastSet', 'ms-Mcs-AdmPwdExpirationTime']:
                val = convert_nt_time(val)
                clear.add(key)

        ldif[-1][key] = val
        clear.add(key)

# errors

if DEBUG: print('clear:', clear, file = sys.stderr)
if DEBUG: print('unclear', unclear, file = sys.stderr)

# get ansible comps

now = datetime.datetime.now()
lag_ansible = datetime.timedelta(days = LAG_ANSIBLE)
lag_msad = datetime.timedelta(days = LAG_MSAD)

ansible = set()
history = {}
computers = {}

fname_hist = sys.argv[2]
with open(fname_hist) as f:
    history = json.load(f)

for r in history['computers']:
    hostname = r['hostname'].split('.')[0].upper()
    computers[hostname] = (r.get('ip', ''), r.get('serial', ''), r.get('mac', ''))
    if parser.parse(r['timestamp']) > now - lag_ansible:
        ansible.add(hostname)

# report

tmp_report = []

for r in ldif:
    if 'DUPLICATE' in r.get('sAMAccountName', ''): continue
    try:
        active = True if parser.parse(r.get('lastLogonTimestamp', '1970-01-01T00:00:01')) > now - lag_msad else False
        tmp_report.append(
            (
            r.get('operatingSystem', ''),
            r.get('dn', ',').split(',', 1)[1],
            r.get('cn', ''),
            r.get('dNSHostName', '').split('.')[0].upper(),
            r.get('lastLogonTimestamp', '1970-01-01T00:00:01'),
            True if r.get('dNSHostName', '').split('.')[0].upper() in ansible else False,
            active)
        )
    except Exception as e:
        if DEBUG: print('parser_error', r, e, file = sys.stderr)
        parser_err_count += 1

tmp_report.sort(key = lambda x: (x[0], x[1], - parser.parse(x[4]).timestamp()))

if DEBUG: print('ldif_len', len(ldif), file = sys.stderr)
if DEBUG: print('parser_err_count', parser_err_count, file = sys.stderr)
if DEBUG: print('report_len', len(tmp_report), file = sys.stderr)

report = {'root': {'computer': []}}

for i, r in enumerate(tmp_report):
    c = computers.get(r[2])
    report['root']['computer'].append({
        'id': i,
        'operatingSystem': r[0],
        'ou': r[1],
        'cn': r[2],
        'dNSHostName': r[3],
        'lastLogonTimestamp': r[4],
        'ansible': r[5],
        'active': r[6],
        'ip': c[0] if c else '',
        'serial': c[1] if c else '',
        'mac': c[2] if c else ''  })

with open(sys.argv[3], 'w', encoding = 'utf-8') as out_file:
    if '.xml' in sys.argv[3]:
        out_file.write(xmltodict.unparse(report, pretty = True))
    elif '.json' in sys.argv[3]:
        out_file.write(json.dumps(report['root'], ensure_ascii=False, indent = 4))
    else:
        os = {}
        for r in  report['root']['computer']:
            os[r['operatingSystem']] = os.get(r['operatingSystem'], 0) + 1
        html = "<html><head></head><body>\n"
        html += "<table border='1' cellpadding='0' cellspacing='0' style='border-collapse:collapse;' table-layout='fixed;'>\n"
        for k, v in os.items():
            k = 'None' if k == '' else k
            html += f"<b>{k}: {v}</b>, " if v > 10 else f"{k}: {v}, "
            html += "&nbsp;&nbsp;"
        html += "<br/><br/>\n"
        html += "<thead><tr>\n"
        for h in report['root']['computer'][0].keys():
            html += f"<th>{h}</th>\n"
        html += "</tr></thead><tbody>\n"
        for r in report['root']['computer']:
            html += "<tr>"
            for c in r.values():
                html += f"<td>{str(c)}</td>"
            "</tr>\n"
        html += "</tbody></table>\n"
        out_file.write(html)
