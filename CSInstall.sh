#!/bin/bash

cat << EOF
*------------------------------------------*
| 888               888       888          |
| 888               888   o   888          |
| 888               888  d8b  888          |
| 888      888  888 888 d888b 888 888  888 |
| 888      888  888 888d88888b888 888  888 |
| 888      888  888 88888P Y88888 888  888 |
| 888      Y88b 888 8888P   Y8888 Y88b 888 |
| 88888888  "Y88888 888P     Y888  "Y88888 |
|  [*] CS 一键部署脚本 360A-team@L.N. [*]  |
*------------------------------------------*
EOF
read -p "[-] 请设置cs下载压缩包url: " csUrl
version="3.13"

rm -rf ./cobaltstrike_$version >/dev/null 2>&1
mkdir cobaltstrike_$version

echo "[-] JAVA环境安装"
echo "deb http://ppa.launchpad.net/webupd8team/java/ubuntu xenial main" | tee /etc/apt/sources.list.d/webupd8team-java.list >/dev/null
echo "deb-src http://ppa.launchpad.net/webupd8team/java/ubuntu xenial main" | tee -a /etc/apt/sources.list.d/webupd8team-java.list >/dev/null
sudo apt-key adv -v --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys EEA14886 >/dev/null 2>&1
sudo apt-get update >/dev/null
echo " |-> sudo apt-get install -y oracle-java8-installer"
sudo apt-get install -y oracle-java8-installer >/dev/null
echo " |-> apt-get install -y oracle-java8-set-default"
sudo apt-get install -y oracle-java8-set-default >/dev/null

echo "[-] 下载cs压缩包"
sudo apt-get install -y unzip >/dev/null
cd cobaltstrike_$version
echo " |-> wget $csUrl"
wget $csUrl >/dev/null 2>&1

echo "[-] 解压cs压缩包"
read -p " |-> 请输入解压密码:" zippassword
unzip -P $zippassword cs3.13.zip >/dev/null

echo "[-] 下载C2profile生成器"
sudo apt-get install -y git >/dev/null
sudo apt-get install -y python >/dev/null
echo " |-> git clone https://github.com/Tycx2ry/Malleable-C2-Randomizer.git"
git clone https://github.com/Tycx2ry/Malleable-C2-Randomizer.git >/dev/null 2>&1
cd Malleable-C2-Randomizer
echo "[-] 生成配置文件"
echo " |-> python malleable-c2-randomizer.py -p SampleTemplates/onedrive.profile -notest"
python malleable-c2-randomizer.py -p SampleTemplates/onedrive.profile -notest >/dev/null
mv onedrive__360ateam.profile ../cobaltstrike3.13/onedrive__360ateam.profile
cd ../cobaltstrike3.13/

echo "[-] 启动teamserver"
sudo apt-get install -y screen >/dev/null
echo " |-> 获取本机IP地址"
ipaddr=$(ip addr | awk '/^[0-9]+: / {}; /inet.*global/ {print gensub(/(.*)\/(.*)/, "\\1", "g", $2)}')
echo " |-> IP: "$ipaddr" 请检测IP地址是否正确并填写"
read -p " |-> 请输入IP地址: " ipaddr
read -p " |-> 请设置连接密码: " password
echo " |-> screen -dmS cs3.13 ./teamserver $ipaddr $password onedrive__360ateam.profile"
chmod +x teamserver
screen -dmS cs3.13 ./teamserver $ipaddr $password onedrive__360ateam.profile

echo "[-] 启动teamserver成功"
echo " -----------------------"
echo " |>IP:       "$ipaddr
echo " |>Port:     8443"
echo " |>Password: "$password
echo " -----------------------"
