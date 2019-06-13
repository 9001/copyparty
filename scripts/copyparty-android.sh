#!/bin/bash
set -e

_msg() { printf "$2"'\033[1;30m>\033[0;33m>\033[1m>\033[0m %s\n' "$1" >&2; }
imsg() { _msg "$1" ''; }
msg() { _msg "$1" \\n; }

mkdir -p ~/src

##
## helper which installs termux packages

termux_upd=y
addpkg() {
	t0=$(date +%s -r ~/../usr/var/cache/apt/pkgcache.bin 2>/dev/null || echo 0)
	t1=$(date +%s)

	[ $((t1-t0)) -gt 600 ] && {
		msg "upgrading termux packages"
		apt update
		apt full-upgrade -y
	}
	msg "installing $1 from termux repos"
	apt install -y $1
}

##
## ensure git and copyparty is available

[ -e ~/src/copyparty/.ok ] || {
	command -v git >/dev/null ||
		addpkg git
	
	msg "downloading copyparty from github"
	(
		cd ~/src
		rm -rf copyparty
		git clone https://github.com/9001/copyparty
		touch copyparty/.ok
	)
}

##
## ensure python is available

command -v python3 >/dev/null ||
	addpkg python

##
## ensure virtualenv and dependencies are available

[ -e ~/src/copyparty/.env/.ok ] || { (
	cd ~/src/copyparty
	rm -rf .env

	msg "creating python3 virtualenv"
	python3 -m venv .env

	msg "installing python dependencies"
	. .env/bin/activate
	pip install jinja2

	deactivate
	touch .env/.ok
) }

##
## add copyparty alias to bashrc

grep -qE '^alias copyparty=' ~/.bashrc 2>/dev/null || {
	msg "adding alias to bashrc"
	echo "alias copyparty='$HOME/copyparty-android.sh'" >> ~/.bashrc
}

##
## start copyparty

imsg "activating virtualenv"
. ~/src/copyparty/.env/bin/activate

imsg "starting copyparty"
PYTHONPATH=~/src/copyparty python3 -m copyparty "$@"

