#!/bin/bash

#配置文件导入
#DIGITALOCEAN_TOKEN
#VULTR_APIKEY
#DOMAIN
#NAMESILO_KEY
#DataBase
DEBUG=1
if [ $DEBUG == 1 ]; then
      source ./test/Config
else
      source ./data/Config
fi


#导入公共函数
source ./includes/functions.sh

#导入vultr相关操作函数
source ./includes/vultr.sh

#导入digitalocean相关操作函数
source ./includes/digitalocean.sh

#导入namesilo相关操作函数
source ./includes/namesilo.sh

#导入DataBase文件相关操作
source ./includes/model.sh


#检测并创建ssh_key
echo "[-] 检测sshkey是否存在"
#$1 vultr_sshkey digitalocean_sshkey
function check_and_create_sshkey(){
     ssh_key_id=$(select_sshkey "$1")
     #echo $ssh_key_id
     #exit
      if [ -z "$ssh_key_id" ];then
            echo "[-] vultr's sskkey isn't exist and to create vultr sshkey."
            #read -p "please to input sshkey's name: " ssh_key_name
            ssh_key_name="redteam_ssh_key"
            if [ "$1" = "vultr_sshkey" ];then
                  ssh_key_id=$(vultr_create_ssh_key "$ssh_key_name")
            elif [ "$1" = "digitalocean_sshkey" ]; then
                  ssh_key_id=$(digitalocean_create_ssh_key "$ssh_key_name")
            fi
            echo "[-] sshkey is created,save sshkey to DataBase file"
            echo "[-] sshkey's id: "$ssh_key_id
            insert_sshkey "$1" "$ssh_key_id" "$ssh_key_name"
      else
            echo "[-] $1 is exist."
            echo "[-] sshkey's id: "$ssh_key_id
      fi
}

check_and_create_sshkey "vultr_sshkey"
check_and_create_sshkey "digitalocean_sshkey"

#$1 cs_1 cs_q mail redirector_c2 redirector_p redirector_q
#$2 vultr digitalocean
function create_server(){
      server_id=$(select_servers_id "$1")
      vultr_sshkey_id=$(select_sshkey "vultr_sshkey")
      digitalocean_sshkey_id=$(select_sshkey "digitalocean_sshkey")
      #read -p "please to input server's hostname: " host_name
      case "$1" in
            "cs_1")
                  host_name="CSServer_1"
                  ;;
            "cs_q")
                  host_name="CSServer_qianfu"
                  ;;
            "mail")
                  host_name="box."$DOMAIN
                  ;;
            "redirector_c2")
                  host_name="Redirector_C2"
                  ;;
            "redirector_p")
                  host_name="Redirector_payload"
                  ;;
            "redirector_q")
                  host_name="Redirector_qianfu"
                  ;;
      esac
      if [ -z "$server_id" ];then       
            ## 创建成功vps，立即获取IP可能获取不到IP，
            ## 所以使用循环获取，知道获取到IP为止。
            if [ "$2" = "digitalocean" ];then
                  server_id=$(digitalocean_create_droplets "$digitalocean_sshkey_id" "$host_name")
                  isExist $server_id "digitalocean_server_id"
                  sleep 6
                  server_ip=$(digitalocean_get_droplets $server_id)
                  while [ -z "$server_ip" ];do
                        server_ip=$(digitalocean_get_droplets $server_id)
                  done
            elif [ "$2" = "vultr" ]; then
                  server_id=$(vultr_create_servers "$vultr_sshkey_id" "$host_name")
                  isExist $server_id "vultr_server_id"
                  sleep 6
                  server_ip=$(vultr_get_servers $server_id)
                  while [ "$server_ip" = "0.0.0.0" ];do
                        server_ip=$(vultr_get_servers $server_id)
                        if [ -z "$server_ip" ]; then
                              $server_ip="0.0.0.0"
                        fi
                  done
            fi
            echo "[-] server id created,save info to DataBase file"
            insert_servers "$1" "$server_id" "$server_ip" "$host_name"
      else
            echo "[-] $host_name server is exist."
            server_ip=$(select_servers_ip "$1")
            if [ -z "$server_ip" ];then
                  echo "[-] server_ip is not exist,to get ip."
                  if [ "$1" = "mail" ]; then
                        server_ip=$(digitalocean_get_droplets $server_id)
                        while [ -z "$server_ip" ];do
                              sleep 3
                              server_ip=$(digitalocean_get_droplets $server_id)
                        done
                  else
                        server_ip=$(vultr_get_servers $server_id)
                        while [ "$server_ip" = "0.0.0.0" ];do
                              sleep 3
                              server_ip=$(vultr_get_servers $server_id)
                              if [ -z "$server_ip" ]; then
                                    $server_ip="0.0.0.0"
                              fi
                        done
                  fi
            fi
            insert_servers "$1" "$server_id" "$server_ip" "$host_name"
            echo "[-] ${host_name}'s ip: "$server_ip
      fi
}

#创建CS服务器
echo "[-] 开始创建CS服务器"
create_server "cs_1" "vultr"

#创建CS潜伏服务器
echo "[-] 开始创建CS潜伏服务器"
create_server "cs_q" "vultr"

#创建邮件前置服务器
echo "[-] 开始创建邮件前置服务器"
create_server "mail" "digitalocean"

#创建上线前置服务器
echo "[-] 开始创建上线前置服务器"
create_server "redirector_p" "vultr"

#创建C2前置服务器
echo "[-] 开始创建C2前置服务器"
create_server "redirector_c2" "vultr"

#创建潜伏前置服务器
echo "[-] 开始创建潜伏前置服务器"
create_server "redirector_q" "vultr"

sleep 1
echo "*------------------------------------*"
echo "  CS服务器:       "$(select_servers_ip 'cs_1')
echo "  CS潜伏服务器:   "$(select_servers_ip 'cs_q')
echo "  邮件前置服务器:  "$(select_servers_ip 'mail')
echo "  上线前置服务器:  "$(select_servers_ip 'redirector_p')
echo "  C2前置服务器:   "$(select_servers_ip 'redirector_c2')
echo "  潜伏前置服务器:  "$(select_servers_ip 'redirector_q')
echo "*------------------------------------*"