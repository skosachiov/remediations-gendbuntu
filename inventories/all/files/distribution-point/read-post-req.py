#!/usr/bin/python3

#
# curl --user "user:pass" --request POST --data '{"key":"value"}' https://example.com/cgi-bin/secure/read-post-req.py
# curl --user "user:pass" --request POST --data-binary @file.json https://example.com/cgi-bin/secure/read-post-req.py
#

import cgi, cgitb, sys, os

cgitb.enable()

post_dir = '/var/www/html/files/post/'

print('Content-type: text/html\n')

ipaddr = cgi.escape(os.environ["REMOTE_ADDR"])
data = sys.stdin.buffer.read()
with open(post_dir + ipaddr + '.post', 'wb') as f:
    f.write(data)

print('OK')