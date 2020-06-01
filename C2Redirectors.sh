#!/bin/bash

# Are we running as root?
if [[ $EUID -ne 0 ]]; then
	echo "This script must be run as root. Did you leave out sudo?"
	exit
fi

function getSelfSignSSL(){
	echo "Create server key..."
	openssl genrsa -des3 -out $1.key 1024
	echo "Create server certificate signing request..."
	#"/C=US/ST=Mars/L=iTranswarp/O=iTranswarp/OU=iTranswarp/CN=$1"
	openssl req -new -subj $2 -key $1.key -out $1.csr
	echo "Remove password..."
	mv $1.key $1.origin.key
	openssl rsa -in $1.origin.key -out $1.key
	echo "Sign SSL certificate..."
	openssl x509 -req -days 3650 -in $1.csr -signkey $1.key -out $1.crt
}


#输入域名
echo "使用域名请先增加A解析"
read -p "DOMAIN: " DOMAIN
#使用自签名或者LetsEncrypt
read -p "[1]自签名;[2]LetsEncrypt: " ssl

filepath=$(pwd)

#环境安装
apt-get install apache2
a2enmod ssl rewrite proxy proxy_http
a2ensite default-ssl.conf
service apache2 stop
sudo apt-get install certbot
sudo apt-get install openssl
sudo apt-get install git
sudo apt-get install python

#自签名
if [[ "$ssl" = "1" ]]; then
	read -p "自签名证书信息[/C=US/ST=Mars/L=iTranswarp/O=iTranswarp/OU=iTranswarp]:" SUBJECT
	SUBJECT=${SUBJECT}"/CN=$DOMAIN"
	getSelfSignSSL $DOMAIN $SUBJECT
	cert=${filepath}"/$DOMAIN.crt"
	privkey=${filepath}"/$DOMAIN.key"
elif [[ "$ssl" = "2" ]]; then
	#LetsEncrypt
	sudo certbot certonly --standalone -d $DOMAIN
	cert="/etc/letsencrypt/live/$DOMAIN/cert.pem"
	privkey="/etc/letsencrypt/live/$DOMAIN/privkey.pem"
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

echo "		SSLCertificateFile      $cert" >>/etc/apache2/sites-enabled/default-ssl.conf
echo "		SSLCertificateKeyFile   $privkey" >>/etc/apache2/sites-enabled/default-ssl.conf
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
read -p "输入c2profie文件路径:" c2profile
read -p "输入c2ServerIP文件路径:" cs2ServerIP
read -p "输入跳转地址[http://www.baidu.com]:" redirect
python cs2modrewrite.py -i $c2profile -c $cs2ServerIP -r $redirect > /var/www/html/.htaccess
service apache2 start