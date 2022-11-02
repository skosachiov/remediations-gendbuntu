import yaml
import os
from ipaddress import *

rootdir = 'inventories/subnets'
suffix = 'vars/main.yml'
outfile = 'inventories/subnets/subnets.yml'

subnets = {"var_subnets": {}}

ip_nets = []

for file in os.listdir(rootdir):
    folder = os.path.join(rootdir, file)
    if os.path.isdir(folder):
        path = os.path.join(folder, suffix)
        with open(path, 'r') as stream:
            try:
                d = yaml.safe_load(stream)
                # print(d)
                if "var_subnets" in d.keys():
                    subnets["var_subnets"][file] = d["var_subnets"]
                    # check subnets
                    for n in d["var_subnets"]:
                        for ip_net in ip_nets:
                            if ip_network(ip_net[0]).subnet_of(ip_network(n)):
                                print(ip_net[1], ip_net[0], "subnet_of", file, n)
                            if ip_network(ip_net[0]).supernet_of(ip_network(n)):
                                print(ip_net[1], ip_net[0], "supernet_of", file, n)
                        ip_nets += [(n, file)]
            except yaml.YAMLError as e:
                print(e)
with open(outfile, 'w') as f:
    f.write("# Please do not modify this file manually, use the script from the utils folder.\n\n")
    f.write(yaml.dump(subnets, default_flow_style=False))
            