#!/usr/bin/python
#
# find . -wholename "*/tasks/main.yml" -exec python "utils/add-tag-to-task-name.py" {} {} \;
# find . -wholename "*/tasks/main/*.yml" -exec python "utils/add-tag-to-task-name.py" {} {} \;

import sys, re

with open(sys.argv[1], "r") as f:
    lines = [line for line in f]

out = []
i = 0
while i < len(lines):
    b = []
    tags_flag = False
    tag = "default"
    while i < len(lines):
        if "tags:" in lines[i]: tags_flag = True
        if tags_flag:
            try:
                tag = re.search("- ([0-9a-z_]{8,64})", lines[i]).group(1)
            except:
                pass
        # if not lines[i].strip(): break
        if tags_flag and "- name:" in lines[i]:
            i -= 1
            break
        b.append(lines[i].rstrip())
        i += 1
    i += 1
    for j in range(len(b)):
        if "- name:" in b[j]:
            if "@" in b[j]:
                b[j] = b[j].split("@")[0].rstrip()
            b[j] += " @" + tag
    for e in b:
        out.append(e + "\n")

with open(sys.argv[2], "w") as fout:
    fout.writelines(out)

