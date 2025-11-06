## echo deb https://deb.debian.org/debian/ stable main >> /etc/apt/sources.list
apt update

HOSTNAME=$(openssl rand -hex 4)
echo $HOSTNAME > /etc/hostname
sed -i "s/127.0.1.1.*/127.0.1.1\t$HOSTNAME/" /etc/hosts

sed -i "s/deb cdrom/# deb cdrom/" /etc/apt/sources.list
echo 'XKBMODEL="pc105"
XKBLAYOUT="us,gb"
XKBVARIANT=","
XKBOPTIONS=""
BACKSPACE="guess"' > /etc/default/keyboard

apt-get -y install keyboard-configuration
apt-get -y install openssh-server vim curl
apt-get -y install systemd-cryptsetup tpm2-tools tpm2-tss-engine-tools dracut gnupg

CRYPTDEV=$(lsblk -rbo NAME | grep crypt)
CRYPTPART=$(blkid -t TYPE=crypto_LUKS -o device)
echo "insecure" > /root/recovery-key.tmp
systemd-cryptenroll --unlock-key-file=/root/recovery-key.tmp --recovery-key --wipe-slot=password $CRYPTPART > /root/recovery-key.weak
chnod 400 /root/recovery-key.weak
systemd-cryptenroll --unlock-key-file=/root/recovery-key.weak --tpm2-device=auto --tpm2-pcrs=0+2 $CRYPTPART
echo add_dracutmodules+=\" tpm2-tss crypt \" > /etc/dracut.conf
sed -i 's/GRUB_CMDLINE_LINUX=""/GRUB_CMDLINE_LINUX="rd.auto rd.luks=1"/' /etc/default/grub
sed -i "s/^/# /"  /etc/crypttab
dracut -f
update-grub

mkdir -p /etc/ansible
echo "localhost ansible_connection=local" >> /etc/ansible/hosts
echo '@reboot root bash -c "sleep 30 && /usr/bin/ansible-pull -i localhost -t dummy -U https://github.com/skosachiov/remediations-gendbuntu.git workstation-test.yml | logger"' >> /etc/cron.d/ansible-pull

