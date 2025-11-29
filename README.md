# Linux Configuration Manager (LCM)

[![ubuntu-20.04](https://github.com/skosachiov/lcm/actions/workflows/ubuntu-20.04.yml/badge.svg)](https://github.com/skosachiov/lcm/actions/workflows/ubuntu-20.04.yml)
[![ubuntu-22.04](https://github.com/skosachiov/lcm/actions/workflows/ubuntu-22.04.yml/badge.svg)](https://github.com/skosachiov/lcm/actions/workflows/ubuntu-22.04.yml)
[![ubuntu-24.04](https://github.com/skosachiov/lcm/actions/workflows/ubuntu-24.04.yml/badge.svg)](https://github.com/skosachiov/lcm/actions/workflows/ubuntu-24.04.yml)
[![rocky-8](https://github.com/skosachiov/lcm/actions/workflows/rocky-8.yml/badge.svg)](https://github.com/skosachiov/lcm/actions/workflows/rocky-8.yml)
[![rocky-9](https://github.com/skosachiov/lcm/actions/workflows/rocky-9.yml/badge.svg)](https://github.com/skosachiov/lcm/actions/workflows/rocky-9.yml)

<img src="https://github.com/skosachiov/lcm/blob/main/lcm.png" width="200" height="250">

# License

This file is part of Linux Configuration Manager (LCM).

Remediations is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Remediations is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Remediations.  If not, see <https://www.gnu.org/licenses/>.

<a name="Introduction"></a>
# Introduction

## Briefly

*The main goal of this project is the configuration and control of various types of devices operating in a corporate environment. Information security is the main direction of development. Roles have default settings that can be dynamically overridden using "inventories" folder rules based on subnet, host group (organizational unit or branch), operating system and so on. Git provides lifecycle. [Roles](#Roles) (policies) can also be used separately.*

## More details

Let's imagine how easy it would be to organise 85000 Ubuntus in the French National Gendarmerie using only two simple but highly popular tools git and ansible. There are two strong arguments in favor of this approach:
- Plenty of ansible specialists in the job market and their salary isn't extremely high
- KISS principle (Unix philosophy)

Obviously there are lot's of ways that could solve individual problems of workstation administrators (ansible galaxy). Although there is no complex solution. There are systems such as Foreman and Saltstack, but Puppet is outdated and Salt hasn't gained popularity yet. AWX (ansible tower) is suitable for servers in push mode. This project offers a complete solution reminiscent of SCCM from the world of Windows, but Ansible replaces Powershell DSC and we have a bonus in the form of version control system git.

It's also important that this project includes inventory data. It's the only possibility to tell about dynamic inventory in ansible-pull mode.

Part of the security elements was taken from ComplianceASCode and OpenSCAP, but these projects are changed for administrators being able to improve code in GIT on daily routine. Roles are provided with readable templates and variables which is different from ComplianceAsCode.

Security, which is one of the main priorities, is provided comprehensively. Leaking of information is blocked by role "dlp": usbguard, switching off modules WiFi and bt. Wide range of settings from remount "tmp" and "home" with options noexec, nodev to checking list of repositories using fingerprints. The most useful thing is the control of mandated access - the control of integrity and signing of performing files. Ideally, every day an information security administrator gets a report with "changed=0" about every workstation, which means that all PCs are in target condition and nothing had to be changed. "Changed!=0" is the cause to concern.

Profiling is performed with certain set of roles:
- workstation (common workstation in enterprise domain)
- mobile-device (laptop for accessing enterprise resources from the Internet)
- flash-drive (bootable flash drive for BYOD)
- distribution-point (distribution point in an enterprise division)
- server (general purpose server)

It's possible to use flags of security in profiles. For example:
- mandatory-access (apparmor, selinux)
- administrative-workstation (group access is restricted)
- network-auditd (send log to the logserver)
- always-on-display (disable lock and turn off display)
- devel-workstation (put the host into test workstation mode)
- unrestricted-os (user can download other operating systems)
- fs-userspace (file systems are available to the user)
- thin-client (thin client mode)
- flash drive (flash-drive thin client mode)
- dist-upgrade (host will force all packages to be updated)

There are a lot of possibilities for information security officers to agree on changes and control the workflow: code review, merge-requests, pull-requests. For example, only an security officer can commit to master branch, see [Lifecycle](#Lifecycle). Ansible-pull agents take playbooks from master branch. There is space for creativity for subdivision gendarmes. Airforce or airtransport can solve their specific problems in separate repositories git and this doesn't cancel basic security settings. On premise Gitlab will be great for collaboration.

Initially, there were several roles responsible for connecting to the proprietary systems like Citrix and Anti-Virus ESET. These roles have been removed from this draft as these roles are of no interest to most admins seeking independence from proprietary software. The subtleties of connecting to the Microsoft AD controller and Exchange were not ruled out, since many organizations are only in the process of transitioning from MS AD to FreeIPA. In addition, this role is applicable to the SambaAD based controller.

The project is adapted for development in the Internet environment with or without corporate repositories. Availability of corporate resources is determined dynamically and the role is adjusted depending on the result.

<a name="Folder structure"></a>
# Folder structure

    ├── inventories         # vars based on various parameters
    │   ├── all             #
    │   │    ├─ group_vars  # vars for certain hosts, for example, for distribution-points
    │   │        └── dp     #
    │   ├── branches        # vars based on Company
    │   ├── ou              # vars based on OU membership
    │   ├── distribution    # vars based on OS distribution
    │   └── subnets         # vars based on Subnet
    │                       #
    ├── roles               # roles
    │   ├── ad-client       #
    │   ├── ansible-client  #
    │   ├── antivirus       #
    │   ├── ...             #
    ├── tests               # test automation
    └── utils               # utilities, git hooks

<a name="Roles"></a>
# Roles

## ad-client

The role prepares a workstation to join a SambaDC or MS AD domain. If you have domain join credentials, you can get full automation. The script for manual attachment is located in /root/realm.sh. FreeIPA client has its own connection mechanism. The role provides additional kerberos logging.

## ansible-client

Ansible-client creates a special user with an authorized key, sets up a sudoers entry, adds a cron job to regularly contact the main ansible git repository.

## antivirus

This role installs and configures a free antivirus suite to run in on-access scan mode and to regularly scan specific folders. The static clamav-dada package is not available in current versions of Ubuntu, and server-side freshclam may require the most recent clamav, so we had to provide the script with an rpm installation. In addition, the script installs onAccess scanning systemd service.

## apt

Apt role controls all packagets on a workstation or mobile device, installs Security task checks repos fingerprints.

## audit

A fairly large role is devoted to setting up an audit. Information security audit is configured in immutable mode, that is, changes require reboot. Additional control is exercised by counting active rules. If the rules are not loaded, the information security officer receives a warning message.

## base-security

Basic device security settings are provided by this role. Corporate and mobile devices are checked and configured daily. Tasks include setting grub security, sudoers, access to various folders and files, checking suid files, and the like.

## base-system

Many small tasks are reduced to one role for setting up the system and the user's working environment. Among them are the installation of corporate certificates, proxy settings, time service, user profile.

## browser

Browser settings moved to a separate role.

## desktop

For convenience, the administrative setting of the user's graphical environment has been moved to a separate role. Here you can pin favorite applications, set desktop wallpaper, set or hide icons in all apps.

## distribution-point

This role is designed to configure and manage regional content distribution points and collect security events.

## dlp

Obviously, the resources of a large enterprise must be protected from leaks. The default dlp setting allows you to connect a keyboard, mouse, headphones, cameras, but blocks any flash drives. The dlp role disables wireless communication modules and some keyjacks radio keyboards. You can always add the necessary devices to the white list.

## fapolicyd

The ansible-controlled version of fapolisyd is an analogue of Applocker on the Windows platform. In addition to the Applocker functions Fapolicy can use file digital signature in combination with IMA/SELinux. In this project, the default fapolicyd role behavior is:
- install fapolicyd
- use whitelist executables using dpkg or rpm database
- use whitelist executables using ansible updated fapolicyd.trust
- prohibit execution of non-whitelisted binary files for regular users
- prevent bytecode and source code from running in runtime environments (OpenJDK, Python, Wine etc.) from the home and tmp folders
- make an exception for root and ansible user
- add executable files from installed deb or rpm to the whitelist daily

## firewall

The firewall role replaces the uncomplicated ufw with the more advanced firewalld, defines multiple zones based on outgoing ip addresses. In addition, the role performs various checks, for example, for suspicious open ports. Configuring the netfilter-persistent package makes it possible to override the default ACCEPT mode for INPUT chains.

## flatpak

Flatpak replaces snap and gives users access to self-contained applications with additional isolation from the file system and the network. In this way, untrusted proprietary applications can be used on the corporate network. In the near future, a role will be added for mirroring external flatpak resources to the corporate network.

## integrity-check

The role configures and controls file integrity checking.

## inventory

The role inventories devices, monitors the health of equipment based on SMART and various voltage and temperature sensors.

## laps

The role of laps is similar to the LAPS service from Microsoft. The difference is that local admin passwords are always encrypted with gpg keys. You can add several gpg keys of information security officers, for example, a master key and a key of a local branch employee. In addition, the data (encrypted passwords) is not stored in the MS AD, but in the network syslog. The role is applied as part of additional security profiles. You may lose access to the device if you don't have network log working and don't have gpg keys to decrypt passwords. If you are absolutely sure, choose: var_laps_dryrun: false.

## mail-client

Evolution is currently being configured to work with EWS services.

## mandatory-access

The SELinux role will be introduced later.

## office

The role is intended for installing and configuring the current version of Libreoffice. Setting and control of macro security level. Choice of Ribbon user interface for all libreoffice applications.

## openvpn-client

The role is designed to securely configure a VPN connection to a corporate network and will be introduced later.

## polkit-restrictions

Events transmitted over d-bus are filtered by this role. The role is related to security.

## pre-tasks

Technical role for dynamic definition of variables.

## print

For each subnet role, connect your own set of printers. See definition of variables.

## remote-assistance

Ansible role produces desktop files in the /usr/share/applications/ folder and creates server no-shell user. Desktop files contain one-liners bash scripts. Desktop files allow to connect in automatic mode reverse forward and direct forward ports over ssh for telework and helpdesk. See https://github.com/skosachiov/linux-remote-assistance repo.

## scap

The role allows information security officers to scan packages installed on users' computers against CVE databases. If the OS distribution is not in a hurry to release fixes for vulnerabilities, you can switch to using self-contained flatpak versions of the software.

## security-modules

At the moment, the role checks the active state of the simplified MAC system apparmor.

## smb-client

For each subnet, network file shares are automatically configured with Kerberos authentication. These can be Samba shares or Windows-based legacy DFS.

## ssh

The secure configuration of the important SSH service has been moved to a separate role.

## terminal-server

The terminal service is provided through XRDP. The role configures accesses, disables insecure protocols, and changes logos.

<a name="Deploy"></a>
# Deploy

## Pre tasks for push mode

1. See inventories/distribution/<distribution>/<major_version>/vars for a list of supported platforms.
2. Create deploy user: `groupadd ansible; useradd -m -g ansible ansible`
3. Set password: `passwd ansible`
4. Add ansible to sudoers: `echo "ansible ALL=(ALL) EXEC:ALL, NOPASSWD:ALL" >> /etc/sudoers`
5. (Ubuntu/Debian) apt install openssh-server

## Deploy Master Distribution Point

IP of the master DP must be in vars to avoid errors. It is advisable to perform the configuration in manual mode.

## Deploy Slave Distribution Points

Create host flag: `touch /etc/ansible/distribution-point`
Slave DP have no ansible gits. IPs of slaves must be in lists to avoid errors.

## Deploy Workstation in install mode

Set the kernel option at the time of installation:
`auto url=<distribution-point-fqdn>`

## Deploy Workstation in push mode

`ANSIBLE_HOST_KEY_CHECKING=False sshpass -p password ansible-playbook -vv --ask-pass -b -i 192.168.122.230, -u ansible workstation.yml`
Regular cron procedures will be configured automatically by default.

If you have not created an ansible user:
`ANSIBLE_HOST_KEY_CHECKING=False sshpass -p password ansible-playbook -vv --ask-pass -e "ansible_become_password=password" -b -i 192.168.122.230, -u admin workstation.yml`

## Deploy workstation in pull mode

wget http://example.test/git/lcm/late-script.sh
sh late-script.sh

## Deploy administrative workstation in pull mode

Create host flag: `touch /etc/ansible/administrative-workstation`
wget http://example.test/git/lcm/late-script.sh
sh late-script.sh

## Deploy workstation mandatory access in pull mode

Create host flag: `touch /etc/ansible/mandatory-access`
wget http://example.test/git/lcm/late-script.sh
sh late-script.sh

## Deploy non-domain PC in push mode

ansible-pull -i localhost -d /root/.ansible/pull/lcm -t mob -U https://example.test/git/lcm mobile-device.yml

## Deploy non-domain PC in pull mode

wget http://example.test/git/lcm/late-script-mob.sh
sh late-script-mob.sh

## Install workstation with preseed.cfg (all data on the disk will be lost)

auto=true priority=critical url=https://github.com/skosachiov/lcm/raw/main/assets/preseed.cfg

## Check Workstation security in push mode

For information security purpose (check only).
`ANSIBLE_HOST_KEY_CHECKING=no sshpass -p password ansible-playbook -vv --check --ask-pass -e "ansible_become_password=password" -b -i 192.168.122.230, -u admin workstation.yml`

## Get changed only tasks in push mode

`ANSIBLE_DISPLAY_OK_HOSTS=no ANSIBLE_DISPLAY_SKIPPED_HOSTS=no sshpass -p password ansible-playbook -v --ask-pass -e "ansible_become_password=password" -b -i 192.168.122.174, -u ansible workstation.yml`

## Set dist-upgrade flag

Create flag: `touch /etc/ansible/dist-upgrade`

<a name="Lifecycle"></a>
# Lifecycle

## All participants

- Clone github repo (once)
`git clone git@github.com:skosachiov/lcm.git`
 or local repo (see man gitolite3)
`git clone gitolite3@ansible.si.mi:lcm`

- Change folder
`cd lcm`

- Edit git config (once)
`git config --global user.email absolon.faucher@si.mi`
`git config --global user.name "Absolon Faucher"`

- Get changes (every time)
`git pull --all`

- View various statuses
`git diff; git log; git status; git branch --all`

## Developer

- The developer needs to make sure it works on the *devel* branch
`git branch -a`
`git checkout devel`

- Make changes
`codium <git folder>` or `vim <file>.yml`

- Commit
`git commit -a -m "some fix"`

- Push changes
`git push --all origin`

## Information security auditor

- The auditor must make sure that he works in the devel branch
`git branch -a`
`git checkout devel`

- Get changes (every time)
`git pull --all`

- Examine the changes in the devel branch relative to the master branch
`git diff master..devel`

- Examine changes at the patch level, if necessary
`git log --patch | less`

- Switch to master branch
`git checkout master`

- Merge devel changes to the current branch (master)
`git merge --no-ff devel`

- Push to the git repo. After that, the tasks will be received and executed by all workstations through the ansible-pull mechanism.
`git push --all origin`

