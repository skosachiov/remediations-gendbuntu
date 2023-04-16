import yaml
import os
import glob
import re
from ipaddress import *

rootdir = 'inventories/subnets'
suffix = 'vars/main.yml'
outfile = 'inventories/subnets/subnets.yml'

subnets = {"var_subnets": {}}

ip_nets = []

for file in glob.iglob(rootdir + "/**/" + suffix, recursive=True):
    # print(file)
    with open(file, 'r') as f:
        try:
            d = yaml.safe_load(f)
            # print(d)
            if "var_subnets" in d.keys():
                subpath = re.sub(rootdir, "", file)
                subpath = re.sub(suffix, "", subpath)
                subpath = subpath.strip("/")
                subnets["var_subnets"][subpath] = d["var_subnets"]
                # check subnets
                for n in d["var_subnets"]:
                    for ip_net in ip_nets:
                        if ip_network(ip_net[0]).subnet_of(ip_network(n)):
                            print(ip_net[1], ip_net[0], "subnet_of", subpath, n)
                        if ip_network(ip_net[0]).supernet_of(ip_network(n)):
                            print(ip_net[1], ip_net[0], "supernet_of", subpath, n)
                    ip_nets += [(n, subpath)]
        except yaml.YAMLError as e:
            print(e)
with open(outfile, 'w') as f:
    f.write("# Please do not modify this file manually, use the script from the utils folder.\n\n")
    f.write(yaml.dump(subnets, default_flow_style=False))


