#!/bin/bash

# $1 SUBID
function vultr_delete_servers(){
      curl -H "API-Key: $VULTR_APIKEY" -s 'https://api.vultr.com/v1/server/destroy' --data "SUBID=$1"
}

# $1 SSHKEYID
function vultr_delete_ssh_key(){
      curl -H "API-Key: $VULTR_APIKEY" -s 'https://api.vultr.com/v1/sshkey/destroy' --data "SSHKEYID=$1"
}

# $1 ssh_key_id
# $2 hostname label
# return vultr_server_id vultr_server_ip
function vultr_create_servers(){
      #创建洛杉矶的vps/ubuntu 18.04 x86_64 512M=200 1G=201 2G=202
      vultr_create_response=$(curl -H "API-Key: $VULTR_APIKEY" -s 'https://api.vultr.com/v1/server/create' --data 'DCID=5' --data 'VPSPLANID=201' --data 'OSID=270' --data 'enable_ipv6=no' --data "SSHKEYID=$1" --data "hostname=$2" --data "label=$2")
      #echo $vultr_create_response
      vultr_server_id=$(echo $vultr_create_response|awk -F'"' '{print $4}')
      #echo $vultr_server_id
      echo $vultr_server_id
}

# $1 vultr_server_id
# retrun vultr_server_ip
function vultr_get_servers(){
      vultr_server_response=$(curl -H "API-Key: $VULTR_APIKEY" -s "https://api.vultr.com/v1/server/list?SUBID=$1")
      #echo $vultr_server_response
      vultr_server_ip=$(echo $vultr_server_response|awk -F'"main_ip":"' '{print $2}'|awk -F'"' '{print $1}')
      echo $vultr_server_ip
}

#$1 name
#retrun ssh_key_id
function vultr_create_ssh_key(){
      public_key=$(cat ~/.ssh/id_rsa.pub)
      ssh_key_response=$(curl -H "API-Key: $VULTR_APIKEY" -s 'https://api.vultr.com/v1/sshkey/create' --data "name=$1" --data "ssh_key=$public_key")
      ssh_key_id=$(echo $ssh_key_response|awk -F'"' '{print $4}')
      echo $ssh_key_id
}