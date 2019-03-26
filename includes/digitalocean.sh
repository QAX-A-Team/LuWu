#!/bin/bash

#digitalocean 删除vps通过tag
function digitalocean_delete_droplets(){
      curl -X DELETE -H "Content-Type: application/json" -H "Authorization: Bearer $DIGITALOCEAN_TOKEN" -s "https://api.digitalocean.com/v2/droplets?tag_name=$1"
}

#digitalocean 删除所有ssh公钥
function digitalocean_delete_ssh_key(){
      ssh_key_response = $(curl -X GET -H "Content-Type: application/json" -H "Authorization: Bearer $DIGITALOCEAN_TOKEN" -s "https://api.digitalocean.com/v2/account/keys")
      #echo $ssh_key_response
      if [ -n "$ssh_key_response" ];then
            total=$(echo $ssh_key_response|awk -F'"total":' '{print $2}'|awk -F'}' '{print $1}')
            if [ $total != 0 ];then
                  for i in $(seq 1 $total); do
                        num=$(expr $i + 1)
                        ssh_key_id=$(echo $ssh_key_response|awk -F'"id":' "{print \$$num}"|awk -F',' '{print $1}')
                        noput=$(curl -X DELETE -H "Content-Type: application/json" -H "Authorization: Bearer $DIGITALOCEAN_TOKEN" -s "https://api.digitalocean.com/v2/account/keys/$ssh_key_id")
                  done
            fi
      fi
}

# digitalocean 创建ssh公钥
function digitalocean_create_ssh_key(){
      public_key=$(cat ~/.ssh/id_rsa.pub)
      ssh_key_response=$(curl -s "https://api.digitalocean.com/v2/account/keys" -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $DIGITALOCEAN_TOKEN" -d "{\"name\":\"$1\",\"public_key\":\"$public_key\"}")
      #echo $ssh_key_response
      ssh_key_id=$(echo $ssh_key_response|awk -F',' '{print $1}'|awk -F':' '{print $3}')
      echo $ssh_key_id
}

# $1 ssh_key_id
# $2 hostname
# return droplets_id
function digitalocean_create_droplets(){
      #创建vps
      create_droplets_response=$(curl -s "https://api.digitalocean.com/v2/droplets" -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $DIGITALOCEAN_TOKEN" -d "{\"name\":\"$2\",\"region\":\"nyc1\",\"size\":\"s-1vcpu-1gb\",\"image\":\"ubuntu-18-04-x64\",\"ssh_keys\":[$1],\"backups\":false,\"ipv6\":false,\"user_data\":null,\"private_networking\":null,\"volumes\": null,\"tags\":[\"$1\"]}")
      #echo $create_droplets_response
      droplets_id=$(echo $create_droplets_response|awk -F',' '{print $1}'|awk -F':' '{print $3}')
      #echo $droplets_id
      echo $droplets_id
}

# $1 droplets_id
# return droplets_ip
function digitalocean_get_droplets(){
      get_droplets_response=$(curl -s "https://api.digitalocean.com/v2/droplets/$1" -X GET -H "Content-Type: application/json" -H "Authorization: Bearer $DIGITALOCEAN_TOKEN")
      #echo $get_droplets_response
      droplets_ip=$(echo $get_droplets_response|awk -F'ip_address' '{print $2}'|awk -F'"' '{print $3}')
      echo $droplets_ip
}

