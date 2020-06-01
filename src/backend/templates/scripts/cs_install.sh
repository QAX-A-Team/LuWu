#!/bin/bash
if [[ $EUID -ne 0 ]]; then
	echo "Please run this script as root" 1>&2
	exit 1
fi
csurl="{{cs_url}}"

{% if zip_pwd %}
zip_pwd="{{zip_pwd}}"
{% endif %}
{% if kill_date %}
kill_date="{{kill_date}}"
{% endif %}

unzip -o cs.zip >/dev/null
cs_pwd="{{cs_pwd}}"

add-apt-repository ppa:openjdk-r/ppa -y
apt-get update -q
apt install -y openjdk-11-jdk curl
apt-get install -y unzip >/dev/null
apt-get install -y wget >/dev/null
apt-get install -y screen >/dev/null
wget $csurl -O cs.zip >/dev/null 2>&1

{% if zip_pwd %}
unzip -oP $zip_pwd cs.zip >/dev/null
{% else %}
unzip -o cs.zip >/dev/null
{% endif %}

ipaddr=$(curl -s icanhazip.com)
chmod +x teamserver
{% if zip_pwd %}
unzip -oP $zip_pwd cs.zip >/dev/null
{% else %}
unzip -o cs.zip >/dev/null
{% endif %}

{% if kill_date %}
screen -dmS cs ./teamserver $ipaddr $cs_pwd ok.profile $kill_date
{% else %}
screen -dmS cs ./teamserver $ipaddr $cs_pwd
{% endif %}
