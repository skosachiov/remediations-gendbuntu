import yaml
import os

rootdir = 'inventories/subnets'
suffix = 'vars/main.yml'
outfile = 'inventories/subnets/subnets.yml'

subnets = {"var_subnets": {}}

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
            except yaml.YAMLError as e:
                print(e)
with open(outfile, 'w') as f:
    f.write("# Please do not modify this file manually, use the script from the utils folder.\n\n")
    f.write(yaml.dump(subnets, default_flow_style=False))

            