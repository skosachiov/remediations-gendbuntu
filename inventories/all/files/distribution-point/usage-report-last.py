from lxml import html
import re

f = open("usage-report.log").readlines()

parsing_a = False
parsing_b = False

users = {}
computers = {}

for line in f:

    if '</table>' in line:
        parsing_a = False
        parsing_b = False
    
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

for i, u in enumerate(sorted(users.items(), key = lambda item: item[1], reverse = True)):
    print(i, u[1], u[0])

for i, c in enumerate(sorted(computers.items(), key = lambda item: item[1], reverse = True)):
    print(i, c[1][0], c[1][1], c[0])
