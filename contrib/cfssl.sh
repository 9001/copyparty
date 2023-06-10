#!/bin/bash
set -e

cat >/dev/null <<'EOF'

NOTE: copyparty is now able to do this automatically;
however you may wish to use this script instead if
you have specific needs (or if copyparty breaks)

this script generates a new self-signed TLS certificate and
replaces the default insecure one that comes with copyparty

as it is trivial to impersonate a copyparty server using the
default certificate, it is highly recommended to do this

this will create a self-signed CA, and a Server certificate
which gets signed by that CA -- you can run it multiple times
with different server-FQDNs / IPs to create additional certs
for all your different servers / (non-)copyparty services

EOF


# ca-name and server-fqdn
ca_name="$1"
srv_fqdn="$2"

[ -z "$srv_fqdn" ] && { cat <<'EOF'
need arg 1: ca name
need arg 2: server fqdn and/or IPs, comma-separated
optional arg 3: if set, write cert into copyparty cfg

example:
  ./cfssl.sh PartyCo partybox.local y
EOF
	exit 1
}


command -v cfssljson 2>/dev/null || {
	echo please install cfssl and try again
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
"names": [{"O":"$ca_name - $srv_fqdn"}]}
EOF
	)|
	cfssl gencert -ca ca.pem -ca-key ca.key \
		-profile=www -hostname="$srv_fqdn" - |
	cfssljson -bare "$srv_fqdn"

	mv "$srv_fqdn-key.pem" "$srv_fqdn.key"
	rm "$srv_fqdn.csr"
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
show "$srv_fqdn.pem"
echo
echo "successfully generated new certificates"

# write cert into copyparty config
[ -z "$3" ] || {
	mkdir -p ~/.config/copyparty
	cat "$srv_fqdn".{key,pem} ca.pem >~/.config/copyparty/cert.pem 
	echo "successfully replaced copyparty certificate"
}


# rm *.key *.pem
# cfssl print-defaults config
# cfssl print-defaults csr
