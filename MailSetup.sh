#!/bin/bash
if [ "`lsb_release -d | sed 's/.*:\s*//' | sed 's/18\.04\.[0-9]/18.04/' `" == "Ubuntu 18.04 LTS" ]; then
	# This machine is running Ubuntu 18.04.
	echo "This machine is running Ubuntu 18.04"
else
	echo "This script must be run on a system running Ubuntu 18.04"
	exit
fi

# Are we running as root?
if [[ $EUID -ne 0 ]]; then
	echo "This script must be run as root. Did you leave out sudo?"
	exit
fi

# Clone the Mail-in-a-Box repository if it doesn't exist.
if [ -d $HOME/mailinabox ]; then
	rm -rf $HOME/mailinabox
fi
if [ ! -f /usr/bin/git ]; then
	echo Installing git . . .
	apt-get -q -q update
	DEBIAN_FRONTEND=noninteractive apt-get -q -q install -y git < /dev/null

	echo
fi

echo Downloading Mail-in-a-Box $TAG. . .
git clone \
	https://github.com/Tycx2ry/mailinabox.git \
	$HOME/mailinabox \
	< /dev/null 2> /dev/null

echo

cd $HOME/mailinabox

#noninteractive install
export NONINTERACTIVE=1
export PUBLIC_IP=auto
export PUBLIC_IPV6=auto
export PRIMARY_HOSTNAME=auto

# Start setup script.
setup/start.sh

