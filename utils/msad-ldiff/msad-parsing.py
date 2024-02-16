#!/usr/bin/python3

# kinit -kt /etc/krb5.keytab SERVER\$@REALM
# ldapsearch -H ldap://dc.example.com -o ldif-wrap=no -E pr=2147483647/noprompt -b "DC=example,DC=com" "(&(objectClass=computer))" > /tmp/msad.ldif
#
# ./msad-parsing.py /tmp/msad.ldif /var/log/usage-report/usage-report-history.json /tmp/msad-report.xml
#

LAG = 14
DEBUG = False

import sys, base64, uuid, struct, datetime, xmltodict, json
from dateutil import parser

ldif = [{}]
clear = set()
unclear = set()

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
if DEBUG: print('unclear:', unclear, file = sys.stderr)

# get ansible comps

now = datetime.datetime.now()
lag = datetime.timedelta(days = LAG)

ansible = set()
history = {}
computers = {}

fname_hist = sys.argv[2]
with open(fname_hist) as f:
    history = json.load(f)

for r in history['computers']:
    hostname = r['hostname'].split('.')[0].upper()
    computers[hostname] = (r.get('ip', ''), r.get('serial', ''), r.get('mac', ''))
    if parser.parse(r['timestamp']) > now - lag:
        ansible.add(hostname)

# report

tmp_report = []

for r in ldif:
    if 'DUPLICATE' in r.get('sAMAccountName', ''): continue
    try:
        if parser.parse(r.get('lastLogonTimestamp')) > now - lag:
            tmp_report.append(
                (
                r.get('operatingSystem', ''),
                r.get('dn').split(',', 1)[1],
                r.get('dNSHostName').split('.')[0].upper(),
                r.get('lastLogonTimestamp'),
                True if r.get('dNSHostName').split('.')[0].upper() in ansible else False )
            )
    except:
        pass

tmp_report.sort(key = lambda x: (x[0], x[1], - parser.parse(x[3]).timestamp()))

report = {'root': {'computer': []}}

for i, r in enumerate(tmp_report):
    c = computers.get(r[2])
    report['root']['computer'].append({
        'id': i,
        'operatingSystem': r[0],
        'ou': r[1],
        'dNSHostName': r[2],
        'lastLogonTimestamp': r[3],
        'ansible': r[4],
        'ip': c[0] if c else '',
        'serial': c[1] if c else '',
        'mac': c[2] if c else ''  })

with open(sys.argv[3], 'w', encoding = 'utf-8') as out_file:
    if '.xml' in sys.argv[3]:
        out_file.write(xmltodict.unparse(report, pretty = True))
    elif '.json' in sys.argv[3]:
        out_file.write(json.dumps(report['root'], indent = 4))
    else:
        os = {}
        for r in  report['root']['computer']:
            os[r['operatingSystem']] = os.get(r['operatingSystem'], 0) + 1
        html = "<html><head></head><body>\n"
        html += "<table border='1' cellpadding='0' cellspacing='0' style='border-collapse:collapse;'>\n"
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
