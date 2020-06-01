#!/bin/bash

function namesilo_unregister_nameserver(){
      noput=$(curl -s "https://www.namesilo.com/api/changeNameServers?version=1&type=xml&key=$NAMESILO_KEY&domain=$DOMAIN&ns1=NS1.DNSOWL.COM&ns2=NS2.DNSOWL.COM")
      noput=$(curl -s "https://www.namesilo.com/api/deleteRegisteredNameServer?version=1&type=xml&key=$NAMESILO_KEY&domain=$DOMAIN&current_host=ns1.box")
      noput=$(curl -s "https://www.namesilo.com/api/deleteRegisteredNameServer?version=1&type=xml&key=$NAMESILO_KEY&domain=$DOMAIN&current_host=ns2.box")
}

function namesilo_register_nameserver(){
      noput=$(curl -s "https://www.namesilo.com/api/addRegisteredNameServer?version=1&type=xml&key=$NAMESILO_KEY&domain=$DOMAIN&new_host=ns1.box&ip1=$1")
      noput=$(curl -s "https://www.namesilo.com/api/addRegisteredNameServer?version=1&type=xml&key=$NAMESILO_KEY&domain=$DOMAIN&new_host=ns2.box&ip1=$1")
}

function namesilo_change_nameserver(){
      noput=$(curl -s "https://www.namesilo.com/api/changeNameServers?version=1&type=xml&key=$NAMESILO_KEY&domain=$DOMAIN&ns1=ns1.box.$DOMAIN&ns2=ns2.box.$DOMAIN")
}