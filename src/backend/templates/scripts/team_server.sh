#!/bin/bash
#
# Start Cobalt Strike Team Server
#

# make pretty looking messages (thanks Carlos)
function print_good () {
    echo -e "\x1B[01;32m[+]\x1B[0m $1"
}

function print_error () {
    echo -e "\x1B[01;31m[-]\x1B[0m $1"
}

function print_info () {
    echo -e "\x1B[01;34m[*]\x1B[0m $1"
}

# check that we're r00t
if [ $UID -ne 0 ]; then
	print_error "Superuser privileges are required to run the team server"
	exit
fi

# check if java is available...
if [ $(command -v java) ]; then
	true
else
	print_error "java is not in \$PATH"
	echo "    is Java installed?"
	exit
fi

# check if keytool is available...
if [ $(command -v keytool) ]; then
	true
else
	print_error "keytool is not in \$PATH"
	echo "    install the Java Developer Kit"
	exit
fi

# generate a certificate
# naturally you're welcome to replace this step with your own permanent certificate.
# just make sure you pass -Djavax.net.ssl.keyStore="/path/to/whatever" and
# -Djavax.net.ssl.keyStorePassword="password" to java. This is used for setting up
# an SSL server socket. Also, the SHA-1 digest of the first certificate in the store
# is printed so users may have a chance to verify they're not being owned.
if [ -e ./cobaltstrike.store ]; then
	print_info "Will use existing X509 certificate and keystore (for SSL)"
else
	print_info "Generating X509 certificate and keystore (for SSL)"
	keytool -keystore ./cobaltstrike.store -storepass 201812 -keypass 201812 -genkey -keyalg RSA -alias cobaltstrike -dname "CN=mail.live.com, OU=Outlook EdgeProxyBAYJune2018, O=Microsoft Corporation, L=Redmond, S=Washington, C=US"
fi

java -XX:ParallelGCThreads=4 -Dcobaltstrike.server_port={{ port }} -Djavax.net.ssl.keyStore=./cobaltstrike.store -Djavax.net.ssl.keyStorePassword=201812 -server -XX:+AggressiveHeap -XX:+UseParallelGC -classpath ./cobaltstrike.jar server.TeamServer $*