#!/bin/bash

#导入公共函数
#source ./includes/functions.sh

# $1 vultr_sshkey or digitalocean_sshkey
# $2 ssh_key_id
# $3 ssh_key_name
insert_sshkey(){
	case "$1" in
    	"vultr_sshkey")
        	row=9
        	;;
    	"digitalocean_sshkey")
			row=10
			;;
	esac
	if [ $(system_check) = "mac" ];then
            sed -i '' "${row}s/#id#.*#id#/#id#$2#id#/g" $DataBase
            sed -i '' "${row}s/#name#.*#name#/#name#$3#name#/g" $DataBase
    else
            sed -i "${row}s/#id#.*#id#/#id#$2#id#/g" $DataBase
            sed -i "${row}s/#name#.*#name#/#name#$3#name#/g" $DataBase
    fi
}

# $1 vultr_sshkey or digitalocean_sshkey
# return ssh_key_id
select_sshkey(){
	ssh_key_id=$(grep "$1" "$DataBase"|awk -F'#id#' '{print $2}')
	echo $ssh_key_id
}

# $1 cs_1 cs_q mail redirector_c2 redirector_p redirector_q
# $2 id
# $3 ip
# $4 tag
insert_servers(){
	case "$1" in
    	"cs_1")
        	row=13
        	;;
    	"cs_q")
			row=12
			;;
		"mail")
			row=3
			;;
		"redirector_c2")
			row=5
			;;
		"redirector_p")
			row=6
			;;
		"redirector_q")
			row=7
			;;
	esac
	if [ $(system_check) = "mac" ];then
		if [ -n "$2" ]; then
			sed -i '' "${row}s/#id#.*#id#/#id#$2#id#/g" $DataBase
		fi
		if [ -n "$3" ]; then
			sed -i '' "${row}s/#ip#.*#ip#/#ip#$3#ip#/g" $DataBase
		fi
		if [ -n "$4" ]; then
			sed -i '' "${row}s/#tag#.*#tag#/#tag#$4#tag#/g" $DataBase
		fi         
    else
        if [ -n "$2" ]; then
			sed -i "${row}s/#id#.*#id#/#id#$2#id#/g" $DataBase
		fi
		if [ -n "$3" ]; then
			sed -i "${row}s/#ip#.*#ip#/#ip#$3#ip#/g" $DataBase
		fi
		if [ -n "$4" ]; then
			sed -i "${row}s/#tag#.*#tag#/#tag#$4#tag#/g" $DataBase
		fi
    fi
}

# $1 cs_1 cs_q mail redirector_c2 redirector_p redirector_q
# return vultr_server_id
select_servers_id(){
	server_id=$(grep "$1" "$DataBase"|awk -F'#id#' '{print $2}')
	echo $server_id
}

# $1 cs_1 cs_q mail redirector_c2 redirector_p redirector_q
# return vultr_server_ip
select_servers_ip(){
	server_ip=$(grep "$1" "$DataBase"|awk -F'#ip#' '{print $2}')
	echo $server_ip
}

# $1 cs_1 cs_q mail redirector_c2 redirector_p redirector_q
# return vultr_server_tag
select_servers_tag(){
	server_tag=$(grep "$1" "$DataBase"|awk -F'#tag#' '{print $2}')
	echo $server_tag
}
 