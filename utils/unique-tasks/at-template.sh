#
# One-liner that applies tasks to thousands of hosts (/tmp/hosts) under the timeout utility control.
# The script splits the list of hosts into chunks (25) and controls the execution of each chunk until the timeout (600s) expires.
# If the timeout is exceeded, the timeout utility kills the ansible-playbook on this iteration.
# This avoids stopping the ansible-playbook due to defunct friezes.
#

ANSIBLE_HOST_KEY_CHECKING=False /bin/bash -c 'while mapfile -n 25 ary && ((${#ary[@]})); do echo "${ary[@]}" | tr -d " " > /tmp/hosts.chunk; timeout 600 /usr/bin/ansible-playbook -v -b -i /tmp/hosts.chunk -u ansible -e "var_url_deb=https://server/files/pkg.deb" /var/www/html/git/lcm/utils/unique-tasks/install-url-deb.yml; done < /tmp/hosts'