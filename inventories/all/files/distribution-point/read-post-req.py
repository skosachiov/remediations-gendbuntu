#!/usr/bin/python3

#
# curl --user "user:pass" --request POST --data '{"key":"value"}' https://example.com/cgi-bin/secure/read-post-req.py
# curl --user "user:pass" --request POST --data-binary @file.json https://example.com/cgi-bin/secure/read-post-req.py
#
# curl --user "user:pass" --request POST --data '{"hostname":"name", "key":"value"}' https://example.com/cgi-bin/secure/read-post-req.py
#

import cgi, cgitb, sys, os, json

cgitb.enable()

post_dir = '/var/www/html/files/post/'

print('Content-type: text/html\n')

ipaddr = cgi.escape(os.environ["REMOTE_ADDR"])
data = sys.stdin.buffer.read()
json_data = json.loads(str(data, 'UTF-8'))
fname = post_dir + json_data.get('hostname', json_data.get('username', ipaddr)).lower() + '.post'
d = {}
if os.path.exists(fname):
    with open(fname) as f:
        d = json.load(f)
    for k in d:
        if isinstance(d[k], list):
            d[k] = list(set(d[k] + json_data.get(k, [])))
else: d = json_data
with open(fname, 'w') as f:
    json.dump(d, f)

print('OK')