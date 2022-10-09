#!/bin/bash

host="paris-ansible"
domain="si.mi"
fqdn="${host}.${domain}"
ip="10.150.1.1"

if ! grep -q "${ip} ${fqdn}" "/etc/hosts"; then
	echo "${ip} ${host}" >> /etc/hosts
	echo "${ip} ${fqdn}" >> /etc/hosts
fi

wget -O - "http://${fqdn}/repos/gpg.key" | apt-key add -

if ! grep -q "ANSIBLE MANAGED BLOCK" "/etc/apt/sources.list"; then
	echo "# BEGIN_LOCAL ANSIBLE MANAGED BLOCK" > /etc/apt/sources.list
	if grep -q "bullseye" "/etc/lsb-release"; then
		echo "deb http://${fqdn}/debian/ bullseye main contrib non-free" >> /etc/apt/sources.list
        echo "deb http://${fqdn}/debian-security bullseye-security main contrib non-free" >> /etc/apt/sources.list
        echo "deb [arch=amd64] http://${fqdn}/repos/bullseye/third-party/ main" >> /etc/apt/sources.list
	fi
	if grep -q "focal" "/etc/lsb-release"; then
    echo "deb http://${fqdn}/focal/repository-main/ focal main contrib non-free" >> /etc/apt/sources.list
		echo "deb http://${fqdn}/focal/repository-update/ focal main contrib non-free" >> /etc/apt/sources.list
		echo "deb http://${fqdn}/focal/repository-base/ focal main contrib non-free" >> /etc/apt/sources.list
		echo "deb http://${fqdn}/focal/repository-extended/ focal main contrib non-free" >> /etc/apt/sources.list
		echo "deb [arch=amd64] http://${fqdn}/repos/buster/debian-security/ focal main" >> /etc/apt/sources.list
		echo "deb [arch=amd64] http://${fqdn}/repos/buster/third-party/ focal main" >> /etc/apt/sources.list
	fi
	echo "# END_LOCAL ANSIBLE MANAGED BLOCK" >> /etc/apt/sources.list
fi

apt update
apt install -y git
apt install -y ansible
apt install -y python
apt install -y openssh-server
apt install -y dnsutils

if [ ! -d /etc/ansible ]; then
  mkdir -p /etc/ansible;
fi
if [ ! -f /etc/ansible/ansible.cfg ]; then
  touch /etc/ansible/ansible.cfg;
fi

if ! grep -q "^log_path\s=" "/etc/ansible/ansible.cfg"; then
	sed -i "s/#log_path\s=\s\/var\/log\/ansible.log/log_path = \/var\/log\/ansible.log/g" /etc/ansible/ansible.cfg
fi

if ! grep -q "BEGIN CERTIFICATE" "/root/https-cert.pem"; then
	cat >> /root/https-cert.pem << EOL
-----BEGIN CERTIFICATE-----
MIIDbTCCAlWgAwIBAgIUVAYtyByzLdp3rXfGLL26LU1FcUgwDQYJKoZIhvcNAQEL
BQAwRTELMAkGA1UEBhMCQVUxEzARBgNVBAgMClNvbWUtU3RhdGUxITAfBgNVBAoM
GEludGVybmV0IFdpZGdpdHMgUHR5IEx0ZDAgFw0yMjA2MTgyMDEzMzVaGA8yMjk2
MDQwMTIwMTMzNVowRTELMAkGA1UEBhMCQVUxEzARBgNVBAgMClNvbWUtU3RhdGUx
ITAfBgNVBAoMGEludGVybmV0IFdpZGdpdHMgUHR5IEx0ZDCCASIwDQYJKoZIhvcN
AQEBBQADggEPADCCAQoCggEBANnPK5xg/z1Ydt63q3iBt6fsWgTyz1cjSCZ51z21
SiznN7QztW/i15y7GoxpaS6XYYG1L2coYgujdaapSsZaR4rvj3aDno2exSdueJjz
tXe/Ke4i5yDaZ+D5+QjXaqeBwT9Ot9UKrDlWCDAuakYXj+U57d4l9Ay16fTvro7n
hF1kq8jJ+t9n0yFVMH35Wpa3GFac6VZVNm8xcxIJMEStjRSnKyL1Xr4hK/Kl3Zw8
gayu4VJCW2OGtoNljUlmirj+i7ih9DfMPPfSPIsTcMRVMXuIHKd2wzSsow5vb8oF
xA5HswPxIfYd+B7cTs7QyEHbwJRJchNBVzTaAalTFWEnDEUCAwEAAaNTMFEwHQYD
VR0OBBYEFFwWCUJTPujGpWlEqgGZ/HDIYtDrMB8GA1UdIwQYMBaAFFwWCUJTPujG
pWlEqgGZ/HDIYtDrMA8GA1UdEwEB/wQFMAMBAf8wDQYJKoZIhvcNAQELBQADggEB
AJu8dBgrZB7OHYja39crXfO4FI6wkEU856xFzBpa1FLqAVm3dOvCfdhXoLbCOoVz
ReiKOWIfFHw1u/iJc7SWUTTceWgEPn9+1JfqCLfS8T2Ws+BS7zX1+PQpJqcVuUhs
y1GZ+fwYlhuc1ApzuIc+X5JM7vHGgrxXyKYdTaDSNvyg9tfCAi51G0CziTON17o+
jd+J8754XcfIqxX4cVTftzRWinjq05OaFKHp6DpVDKhKPBkhV22jh8BD3txNRo2H
1d6KksOKbLVCZL6HXOcihUnbLAbR3dRWtkUGmp/0DczIlUKraL/EuD2gSLYJYHil
y3LHgKE/8WU+/p6+tjWdRHM=
-----END CERTIFICATE-----
EOL
	echo "[http]" > /root/.gitconfig
	echo "    sslCAinfo = /root/https-cert.pem" >> /root/.gitconfig
fi

if ! grep -q "localhost ansible_connection=local" "/etc/ansible/hosts"; then
	echo "localhost ansible_connection=local" >> /etc/ansible/hosts
fi

# if ! grep -q "ansible-pull" "/etc/cron.d/ansible-pull"; then
if ! grep -q "remediations-gendbuntu" "/etc/cron.d/ansible-pull"; then
	echo '@reboot root bash -c "sleep 60 && uname -a | logger -n '${fqdn}'"' > /etc/cron.d/ansible-pull
	echo '@reboot root bash -c "sleep 60 && /usr/bin/ansible-pull -i localhost -U https://'${fqdn}'/git/remediations-gendbuntu | logger -n '${fqdn}'"' >> /etc/cron.d/ansible-pull
	echo '# EOF' >> /etc/cron.d/ansible-pull
fi

if ! grep -q "auto eth0" "/etc/network/interfaces"; then
	echo "auto eth0" >> /etc/network/interfaces
	echo "iface eth0 inet dhcp" >> /etc/network/interfaces
fi


