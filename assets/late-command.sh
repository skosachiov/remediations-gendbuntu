## echo deb https://deb.debian.org/debian/ stable main >> /etc/apt/sources.list
apt update
	
HOSTNAME=$(openssl rand -hex 4)
echo $HOSTNAME > /etc/hostname
sed -i "s/127.0.1.1.*/127.0.1.1\t$HOSTNAME/" /etc/hosts
	
sed -i "s/deb cdrom/# deb cdrom/" /etc/apt/sources.list
echo 'XKBMODEL="pc105"
XKBLAYOUT="us,fr"
XKBVARIANT=","
XKBOPTIONS=""
BACKSPACE="guess"' > /etc/default/keyboard
apt-get -y install keyboard-configuration

apt-get -y install openssh-server vim

apt-get -y install systemd-cryptsetup tpm2-tools tpm2-tss-engine-tools dracut gnupg

CRYPTDEV=$(lsblk -rbo NAME | grep _crypt)
CRYPTPART=$(blkid -t TYPE=crypto_LUKS -o device)
openssl rand -hex 4096 > /tmp/unlock-key-file
cp /tmp/unlock-key-file /etc/unlock-key-file.backup
chmod 400 /tmp/unlock-key-file
echo insecure | cryptsetup luksAddKey $CRYPTPART /tmp/unlock-key-file
systemd-cryptenroll --unlock-key-file=/tmp/unlock-key-file --tpm2-device=auto --tpm2-pcrs=0+1+2 $CRYPTPART
cryptsetup --key-file=/tmp/unlock-key-file luksKillSlot $CRYPTPART 0
rm -f /boot/efi/unlock-key-file.gpg
gpg --encrypt --recipient-file /etc/apt/keyrings/corpos_repo.asc --output /boot/efi/unlock-key-file.gpg < /tmp/unlock-key-file
echo add_dracutmodules+=\" tpm2-tss crypt \" > /etc/dracut.conf
sed -i 's/GRUB_CMDLINE_LINUX=""/GRUB_CMDLINE_LINUX="rd.auto rd.luks=1"/' /etc/default/grub
sed -i "s/^/# /"  /etc/crypttab
dracut -f
update-grub

echo "localhost ansible_connection=local" >> /etc/ansible/hosts
echo '@reboot root bash -c "sleep 30 && /usr/bin/ansible-pull -i localhost -U https://github.com/skosachiov/remediations-gendbuntu/raw/main/workstation-test.yml -t dummy"' >> /etc/cron.d/ansible-pull

