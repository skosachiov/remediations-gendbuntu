#!/usr/bin/python3

import cgi

from lxml import html
import re
import string

f = open("usage-report.log").readlines()

parsing_a = False
parsing_b = False

users = {}
computers = {}

for line in f:

    if '</table>' in line:
        parsing_a = False
        parsing_b = False
    
    if '</td><td>' in line:
        try:
            if parsing_a:
                tree = html.fromstring(line)
                td = tree.xpath("./td/text()")
                user = re.search("user=(.*)", td[2]).group(1)
                user = re.sub("@.*", "", user)
                user = re.sub(".*\\\\", "", user)
                users[user.lower()] = td[0]
            if parsing_b:
                tree = html.fromstring(line)
                td = tree.xpath("./td/text()")
                computer = re.search("(.*)\.?", td[3]).group(1)
                computer = re.sub("\..*", "", computer)
                computers[computer.lower()] = [td[0], td[9]]
        except:
            pass
        
    if "Authentication success</h1>" in line:
        parsing_a = True
    if "Basic ansible facts</h1>" in line:
        parsing_b = True

a_a, a_b = [], []

for i, u in enumerate(sorted(users.items(), key = lambda item: item[1], reverse = True)):
    a_a.append([str(i), u[1], u[0]])

for i, c in enumerate(sorted(computers.items(), key = lambda item: item[1], reverse = True)):
    a_b.append([str(i), c[1][0], c[1][1], c[0]])

print("Content-type: text/html; charset=utf-8")
print("Cache-Control: no-cache")
print()
header = """
<html><head>
<link type="text/css" rel="stylesheet" href="/javascript/jquery-tablesorter/css/theme.default.css" />
<script type="text/javascript" src="/javascript/jquery/jquery.min.js"></script>
<script type="text/javascript" src="/javascript/jquery-tablesorter/jquery.tablesorter.min.js"></script>
<script type="text/javascript">
    $(function(){ $("#a_a").tablesorter(); });
    $(function(){ $("#a_b").tablesorter(); });
</script>
</head><body>
<div class="container">
"""
print(header)

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

print("<a href='#h_a_a'>Last authentication success</a>")
print("<a href='#h_a_b'>Last basic ansible facts</a>")

print("<br />")
print("<h1 id='h_a_a'>Last authentication success</h1>")
print_table(a_a, "a_a")

print("<br />")
print("<h1 id='h_a_b'>Last basic ansible fact</h1>")
print_table(a_b, "a_b")