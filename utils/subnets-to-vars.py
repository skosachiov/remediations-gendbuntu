import yaml
import os

rootdir = 'inventories/subnets/'
subnetsfile = 'subnets.yml'
mainfile = '/vars/main.yml'
newfile = '/vars/new.yml'

d = {}

with open(rootdir + subnetsfile, 'r') as stream:
    try:
        d = yaml.safe_load(stream)
    except yaml.YAMLError as e:
        print(e)

for key in d['var_subnets'].keys():
    print(key)
    os.system('echo "var_subnets:" > ' + rootdir + key + newfile)
    for s in d['var_subnets'][key]:
        print(s)
        os.system('echo "  - ' + s + '" >> ' + rootdir + key + newfile)
    os.system('echo "var_contacts:" >> ' + rootdir + key + newfile)
    os.system('echo "  - dummy.contact" >> ' + rootdir + key + newfile)
    os.system('cat ' + rootdir + key + mainfile + ' >> ' + rootdir + key + newfile)

        
