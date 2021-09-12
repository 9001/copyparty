#!/bin/bash
set -e

# ca-name and server-name
ca_name="$1"
srv_name="$2"

[ -z "$srv_name" ] && {
	echo "need arg 1: ca name"
	echo "need arg 2: server name"
	echo "optional arg 3: if set, write cert into copyparty cfg"
	exit 1
}


gen_ca() {
	(tee /dev/stderr <<EOF
{"CN": "$ca_name ca",
"CA": {"expiry":"87600h", "pathlen":0},
"key": {"algo":"rsa", "size":4096},
"names": [{"O":"$ca_name ca"}]}
EOF
	)|
	cfssl gencert -initca - |
	cfssljson -bare ca
	
	mv ca-key.pem ca.key
	rm ca.csr
}


gen_srv() {
	(tee /dev/stderr <<EOF
{"key": {"algo":"rsa", "size":4096},
"names": [{"O":"$ca_name - $srv_name"}]}
EOF
	)|
	cfssl gencert -ca ca.pem -ca-key ca.key \
		-profile=www -hostname="$srv_name.$ca_name" - |
	cfssljson -bare "$srv_name"

	mv "$srv_name-key.pem" "$srv_name.key"
	rm "$srv_name.csr"
}


# create ca if not exist
[ -e ca.key ] ||
	gen_ca

# always create server cert
gen_srv


# dump cert info
show() {
	openssl x509 -text -noout -in $1 |
	awk '!o; {o=0} /[0-9a-f:]{16}/{o=1}'
}
show ca.pem
show "$srv_name.pem"


# write cert into copyparty config
[ -z "$3" ] || {
	mkdir -p ~/.config/copyparty
	cat "$srv_name".{key,pem} ca.pem >~/.config/copyparty/cert.pem 
}


# rm *.key *.pem
# cfssl print-defaults config
# cfssl print-defaults csr
