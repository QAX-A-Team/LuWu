#!/bin/bash

# Are we running as root?
if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root. Did you leave out sudo?"
  exit
fi


function getSelfSignSSL() {
    openssl genrsa -des3 -passout pass:test -out $DOMAIN.key 1024
    echo "Create server certificate signing request..."
    SUBJECT="/C=US/ST=Mars/L=iTranswarp/O=iTranswarp/OU=iTranswarp/CN=$DOMAIN"
    openssl req -passin pass:test -new -subj $SUBJECT -key $DOMAIN.key -out $DOMAIN.csr
    echo "Remove password..."
    mv $DOMAIN.key $DOMAIN.origin.key
    openssl rsa -passin pass:test -in $DOMAIN.origin.key -out $DOMAIN.key
    echo "Sign SSL certificate..."
    openssl x509 -req -days 3650 -in $DOMAIN.csr -signkey $DOMAIN.key -out $DOMAIN.crt
}


#输入域名
echo "使用域名请先增加A解析"
DOMAIN="{{domain}}"
#使用自签名或者LetsEncrypt
ssl="{{ssl}}"
filepath=$(pwd)

#环境安装
apt-get install -y apache2 certbot openssl python git
a2enmod ssl rewrite proxy proxy_http
a2ensite default-ssl.conf
service apache2 stop

#自签名
if [[ "$ssl" = "1" ]]; then
    getSelfSignSSL
    cert=${filepath}"/$DOMAIN.crt"
    privkey=${filepath}"/$DOMAIN.key"
elif [[ "$ssl" = "2" ]]; then
    acme.sh --issue -d $DOMAIN --standalone

    acme.sh --install-cert -d $DOMAIN \
    --cert-file /opt/$DOMAIN.crt  \
    --key-file /opt/$DOMAIN.key  \
    --ca-file /opt/ca.crt

    cert="/opt/$DOMAIN.crt"
    privkey="/opt/$DOMAIN.key"
else
    echo "ssl选择错误"
    exit
fi

#修改apache配置端口是80和443
cat > /etc/apache2/sites-enabled/000-default.conf <<EOF
<VirtualHost *:80>
    ServerAdmin webmaster@localhost
    DocumentRoot /var/www/html
    <Directory /var/www/html>
            Options Indexes FollowSymLinks MultiViews
               AllowOverride All
            Order allow,deny
            allow from all
    </Directory>
    ErrorLog ${APACHE_LOG_DIR}/error.log
    CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>
EOF

cat > /etc/apache2/sites-enabled/default-ssl.conf <<EOF
<IfModule mod_ssl.c>
    <VirtualHost _default_:443>
        ServerAdmin webmaster@localhost
        DocumentRoot /var/www/html
        ErrorLog ${APACHE_LOG_DIR}/error.log
        CustomLog ${APACHE_LOG_DIR}/access.log combined
        <Directory /var/www/html>
                Options Indexes FollowSymLinks
                  AllowOverride All
                Require all granted
        </Directory>
        SSLEngine on
        SSLProxyEngine On
        SSLProxyVerify none
        SSLProxyCheckPeerCN off
        SSLProxyCheckPeerName off
EOF

echo "    SSLCertificateFile      $cert" >>/etc/apache2/sites-enabled/default-ssl.conf
echo "    SSLCertificateKeyFile   $privkey" >>/etc/apache2/sites-enabled/default-ssl.conf
cat >> /etc/apache2/sites-enabled/default-ssl.conf <<EOF
        <FilesMatch "\.(cgi|shtml|phtml|php)$">
                SSLOptions +StdEnvVars
        </FilesMatch>
        <Directory /usr/lib/cgi-bin>
                SSLOptions +StdEnvVars
        </Directory>
    </VirtualHost>
</IfModule>
EOF

git clone https://github.com/Tycx2ry/cs2modrewrite.git
cd cs2modrewrite

c2profile={{c2_profile}}
cs2ServerIP={{cs2_server_ip}}

redirect={{redirect}}

python cs2modrewrite.py -i $c2profile -c $cs2ServerIP -r $redirect > /var/www/html/.htaccess
service apache2 start
# service apache2 force-reload