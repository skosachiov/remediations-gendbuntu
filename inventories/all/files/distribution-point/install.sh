#!/bin/bash

apachedir=/var/www/html
cgibin=/usr/lib/cgi-bin
gitdir=$apachedir/git

chown -R www-data:www-data $apachedir/security
chmod -R a+r $apachedir/security

chown -R www-data:www-data $gitdir
chmod -R a+r $gitdir
# see late-script.sh
# wget http://ansible.si.mi/https-cert.pem
# git config --global http.sslCAInfo ~/https-cert.pem
cp -f https-cert.pem $apachedir/

cp -f gpg.key $apachedir/repos/

cp -f preseed.cfg $apachedir/d-i/squeeze/
cp -f late-script.sh $apachedir/d-i/squeeze/
# make-ssl-cert generate-default-snakeoil --force-overwrite
# cp -f /etc/ssl/certs/ssl-cert-snakeoil.pem $gitdir/remediations-gendbuntu/

cp -f usage-report.py $cgibin/
chmod a+x $cgibin/usage-report.py

systemctl restart apache2
