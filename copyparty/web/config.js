/* ToDo: 
get searchable commands on demand by searching via xhr, like file search,
OR hand over this list generated from within httpcli.py or something
(remove the hard-coded arg lists in this file afterwards)

read current config and hand over from httpcli.py on page load or on button press

import from command string(?)

export: better indication / user guidance

add config for user groups

indicate that users without pw are usable for external identity providers, possibly linking it to the setting that enables idps

require usernames checkbox setting

finally, remove the disclaimer banner
*/

"use strict";

var J_CFG = 1;

class Argument {
    constructor(cmd, help) {
        this.cmd = cmd;
        this.help = help;
    }
}

/* FLAGS update instructions

to update manually from the documentation:
copy what makes sense from the cli help page
https://copyparty.eu/cli/

open VS code search
filter for file: flags*

replace
^[a-z].*
with nothing

replace (careful there are spaces after the \n that you need to copy too)
\n                   
with nothing

replace (optional)
\n\n
with
\n
(twice)

replace
\\
with
\\\\

replace
\$
with
\\\$

replace
"
with
\\"

replace
^\s*(-\S+).*?\s{2,}(.*)$
with
  new Argument("$1", "$2"),

*/

var flags = [
    new Argument("-c", "REPEATABLE: add config file (default: [])"),
    new Argument("-nc", "max num clients (default: 1024)"),
    new Argument("-a", "REPEATABLE: add account, USER:PASS; example [ed:wark] (default: None)"),
    new Argument("-v", "REPEATABLE: add volume, SRC:DST:FLAG; examples [.::r], [/mnt/nas/music:/music:r:aed], see --help-accounts (default: None)"),
    new Argument("--grp", "REPEATABLE: add group, NAME:USER1,USER2,...; example [admins:ed,foo,bar] (default: None)"),
    new Argument("--usernames", "require username and password for login; default is just password (default: False)"),
    new Argument("--chdir", "change working-directory to PATH before mapping volumes (default: None)"),
    new Argument("-ed", "enable the ?dots url parameter / client option which allows clients to see dotfiles / hidden files (volflag=dots) (default: False)"),
    new Argument("--urlform", "how to handle url-form POSTs; see --help-urlform (default: print,xm)"),
    new Argument("--wintitle", "server terminal title, for example [\$ip-10.1.2.] or [\$ip-] (default: cpp @ \$pub)"),
    new Argument("--name", "server name (displayed topleft in browser and in mDNS) (default: hostname)"),
    new Argument("--name-url", "URL for server name hyperlink (displayed topleft in browser) (default: None)"),
    new Argument("--site", "public URL to assume when creating links; example: [https://example.com/] (default: )"),
    new Argument("--env-expand", "expand environment-variables in config-files? [0]=no, [1]=\$VAR (old scary syntax), [2]=\${VAR} (new recommended syntax); default is new-syntax with panic if old-syntax is seen (default: -1)"),
    new Argument("--mime", "REPEATABLE: map file EXTension to MIMEtype, for example [jpg=image/jpeg] (default: None)"),
    new Argument("--mimes", "list default mimetype mapping and exit (default: False)"),
    new Argument("--rmagic", "do expensive analysis to improve accuracy of returned mimetypes; will make file-downloads, rss, and webdav slower (volflag=rmagic) (default: False)"),
    new Argument("-j", "num cpu-cores for uploads/downloads (0=all); keeping the default is almost always best (default: 1)"),
    new Argument("--reload-sig", "reload server config when unix-signal S is received; examples: [SIGUSR1], [USR1], [10] (default: USR1)"),
    new Argument("--vc-url", "URL to check for vulnerable versions (default-disabled) (default: )"),
    new Argument("--vc-age", "how many hours to wait between vulnerability checks (default: 3)"),
    new Argument("--vc-sev", "minimum severity to care about; one of these: low medium high critical (default: low)"),
    new Argument("--vc-exit", "panic and exit if current version is vulnerable (default: False)"),
    new Argument("--license", "show licenses and exit (default: False)"),
    new Argument("--version", "show versions and exit (default: False)"),
    new Argument("--versionb", "show version and exit (default: False)"),
    new Argument("-i", "IPs and/or unix-sockets to listen on (comma-separated list; see --help-bind). Default: all IPv4 and IPv6 (default: ::)"),
    new Argument("-p", "ports to listen on (comma/range); ignored for unix-sockets (default: 3923)"),
    new Argument("--ll", "include link-local IPv4/IPv6 in mDNS replies, even if the NIC has routable IPs (breaks some mDNS clients) (default: False)"),
    new Argument("--rproxy", "which ip to associate clients with; [0]=tcp, [1]=origin (first x-fwd, unsafe), [-1]=closest-proxy, [-2]=second-hop, [-3]=third-hop (default: 9999999)"),
    new Argument("--xff-hdr", "if reverse-proxied, which http header to read the client's real ip from (default: x-forwarded-for)"),
    new Argument("--xf-host", "if reverse-proxied, which http header to read the correct Host value from; this header must contain the server's external domain name (default: x-forwarded-host)"),
    new Argument("--xf-proto", "if reverse-proxied, which http header to read the correct protocol value from; this header must contain either 'http' or 'https' (default: x-forwarded-proto)"),
    new Argument("--xf-proto-fb", "protocol to assume if the X-Forwarded-Proto header (--xf-proto) is not provided by the reverseproxy; either 'http' or 'https' (default: )"),
    new Argument("--xff-src", "list of trusted reverse-proxy CIDRs (comma-separated); only accept the real-ip header (--xff-hdr) and IdP headers if the incoming connection is from an IP within either of these subnets. Specify [lan] to allow all LAN / private / non-internet IPs. Can be disabled with [any] if you are behind cloudflare (or similar) and are using --xff-hdr=cf-connecting-ip (or similar) (default: 127.0.0.0/8, ::1/128)"),
    new Argument("--ipa", "only accept connections from IP-addresses inside CIDR (comma-separated); examples: [lan] or [10.89.0.0/16, 192.168.33.0/24] └─for performance and security, this only looks at the TCP/Network-level IP, and will NOT work behind a reverseproxy  (default: )"),
    new Argument("--ipar", "only accept connections from IP-addresses inside CIDR (comma-separated). └─this is reverseproxy-compatible; reads client-IP from 'X-Forwarded-For' if possible, with TCP/Network IP as  fallback (default: )"),
    new Argument("--rp-loc", "if reverse-proxying on a location instead of a dedicated domain/subdomain, provide the base location here; example: [/foo/bar] (default: )"),
    new Argument("--cachectl", "default-value of the 'Cache-Control' response-header (controls caching in webbrowsers). Default prevents repeated downloading of the same file unless necessary (browser will ask copyparty if the file has changed). Examples: [max-age=604869] will cache for 7 days, [no-store, max-age=0] will always redownload. (volflag=cachectl) (default: no-cache)"),
    new Argument("--http-vary", "value of the 'Vary' response-header; a hint for caching proxies (default: Origin, PW, Cookie)"),
    new Argument("--http-no-tcp", "do not listen on TCP/IP for http/https; only listen on unix-domain-sockets (default: False)"),
    new Argument("--freebind", "allow listening on IPs which do not yet exist, for example if the network interfaces haven't finished going up. Only makes sense for IPs other than '0.0.0.0', '127.0.0.1', '::', and '::1'. May require running as root (unless net.ipv6.ip_nonlocal_bind) (default: False)"),
    new Argument("--wr-h-eps", "write list of listening-on ip:port to textfile at PATH when http-servers have started (default: )"),
    new Argument("--wr-h-aon", "write list of accessible-on ip:port to textfile at PATH when http-servers have started (default: )"),
    new Argument("--s-thead", "socket timeout (read request header) (default: 120)"),
    new Argument("--s-tbody", "socket timeout (read/write request/response bodies). Use 60 on fast servers (default is extremely safe). Disable with 0 if reverse-proxied for a 2% speed boost (default: 128.0)"),
    new Argument("--s-rd-sz", "socket read size in bytes (indirectly affects filesystem writes; recommendation: keep equal-to or lower-than --iobuf) (default: 262144)"),
    new Argument("--s-wr-sz", "socket write size in bytes (default: 262144)"),
    new Argument("--s-wr-slp", "debug: socket write delay in seconds (default: 0.0)"),
    new Argument("--rsp-slp", "debug: response delay in seconds (default: 0.0)"),
    new Argument("--rsp-jtr", "debug: response delay, random duration 0..SEC (default: 0.0)"),
    new Argument("--list-nics", "debug: list detected network adapters (default: False)"),
    new Argument("--list-ips", "debug: list detected LAN IPs (default: False)"),
    new Argument("--http-only", "disable ssl/tls -- force plaintext (default: False)"),
    new Argument("--https-only", "disable plaintext -- force tls (default: False)"),
    new Argument("--cert", "path to file containing a concatenation of TLS key and certificate chain (if --certkey is not set), or just the certificate chain (if --certkey is set) (default: ~/.config/copyparty/cert.pem)"),
    new Argument("--certkey", "path to file containing just the certificate key; if this is set, then --cert should only contain the certificate chain (default: )"),
    new Argument("--ssl-ver", "set allowed ssl/tls versions; [help] shows available versions; default is what your python version considers safe (default: )"),
    new Argument("--ciphers", "set allowed ssl/tls ciphers; [help] shows available ciphers (default: )"),
    new Argument("--ssl-dbg", "dump some tls info (default: False)"),
    new Argument("--ssl-log", "log master secrets for later decryption in wireshark (default: )"),
    new Argument("--no-crt", "disable automatic certificate creation (default: False)"),
    new Argument("--crt-ns", "comma-separated list of FQDNs (domains) to add into the certificate (default: )"),
    new Argument("--crt-exact", "do not add wildcard entries for each --crt-ns (default: False)"),
    new Argument("--crt-noip", "do not add autodetected IP addresses into cert (default: False)"),
    new Argument("--crt-nolo", "do not add 127.0.0.1 / localhost into cert (default: False)"),
    new Argument("--crt-nohn", "do not add mDNS names / hostname into cert (default: False)"),
    new Argument("--crt-dir", "where to save the CA cert (default: ~/.config/copyparty)"),
    new Argument("--crt-cdays", "ca-certificate expiration time in days (default: 3650.0)"),
    new Argument("--crt-sdays", "server-cert expiration time in days (default: 365.0)"),
    new Argument("--crt-cn", "CA/server-cert common-name (default: partyco)"),
    new Argument("--crt-cnc", "override CA name (default: --crt-cn)"),
    new Argument("--crt-cns", "override server-cert name (default: --crt-cn cpp)"),
    new Argument("--crt-back", "backdate in hours (default: 72.0)"),
    new Argument("--crt-alg", "algorithm and keysize; one of these: ecdsa-256 rsa-4096 rsa-2048 (default: ecdsa-256)"),
    new Argument("--idp-h-usr", "REPEATABLE: bypass the copyparty authentication checks if the request-header HN contains a username to associate the request with (for use with authentik/oauth/...)WARNING: if you enable this, make sure clients are unable to specify this header themselves; must be washed away and replaced by a reverse-proxy (default: None)"),
    new Argument("--idp-hm-usr", "REPEATABLE: bypass the copyparty authentication checks if the request-header T is provided, and its value exists in a mapping defined by this option; see --help-idp (default: None)"),
    new Argument("--idp-h-grp", "assume the request-header HN contains the groupname of the requesting user; can be referenced in config files for group-based access control (default: )"),
    new Argument("--idp-h-key", "optional but recommended safeguard; your reverse-proxy will insert a secret header named HN into all requests, and the other IdP headers will be ignored if this header is not present (default: )"),
    new Argument("--idp-gsep", "if there are multiple groups in --idp-h-grp, they are separated by one of the characters in RE (default: |:;+,)"),
    new Argument("--idp-chsub", "characters to replace in usernames/groupnames; a list of pairs of characters separated by | so for example | _| will replace spaces with _ to make configuration easier, or |%_|^_|@_| will replace %/^/@ with _ (default: )"),
    new Argument("--idp-db", "where to store the known IdP users/groups (if you run multiple copyparty instances, make sure they use different DBs) (default: ~/.config/copyparty/idp.db)"),
    new Argument("--idp-store", "how to use --idp-db; [0] = entirely disable, [1] = write-only (effectively disabled), [2] = remember users, [3] = remember users and groups.NOTE: Will remember and restore the IdP-volumes of all users for all eternity if set to 2 or 3, even when user is deleted from your IdP (default: 1)"),
    new Argument("--idp-adm", "comma-separated list of users allowed to use /?idp (the cache management UI) (default: )"),
    new Argument("--idp-cookie", "generate a session-token for IdP users which is written to cookie cppws (or cppwd if plaintext), to reduce the load on the IdP server, lifetime S seconds. └─note: The expiration time is a client hint only; the actual lifetime of the session-token is infinite (until next  restart with --ses-db wiped) (default: 0)"),
    new Argument("--idp-login", "replace all login-buttons with a link to URL L (unless pw is in --auth-ord then both will be shown); [{dst}] expands to url of current page (default: )"),
    new Argument("--idp-login-t", "the label/text for the idp-login button (default: Login with SSO)"),
    new Argument("--idp-logout", "replace all logout-buttons with a link to URL L (default: )"),
    new Argument("--auth-ord", "controls auth precedence; examples: [pw,idp,ipu], [ipu,pw,idp], see --help-auth-ord (default: idp,ipu)"),
    new Argument("--pw-hdr", "lowercase name of password-header (NAME: foo); WARNING: Changing this will break support for many clients (default: pw)"),
    new Argument("--pw-urlp", "lowercase name of password url-param (?NAME=foo); WARNING: Changing this will break support for many clients (default: pw)"),
    new Argument("--no-bauth", "disable basic-authentication support; do not accept passwords from the 'Authenticate' header at all. NOTE: This breaks support for the android app (default: False)"),
    new Argument("--bauth-last", "keeps basic-authentication enabled, but only as a last-resort; if a cookie is also provided then the cookie wins (default: False)"),
    new Argument("--ses-db", "where to store the sessions database (if you run multiple copyparty instances, make sure they use different DBs) (default: ~/.config/copyparty/sessions.db)"),
    new Argument("--ses-len", "session key length; default is 120 bits ((20//4)*4*6) (default: 20)"),
    new Argument("--no-ses", "disable sessions; use plaintext passwords in cookies (default: False)"),
    new Argument("--grp-all", "the name of the auto-generated group which contains every username which is known (default: acct)"),
    new Argument("--ipu", "REPEATABLE: users with IP matching CIDR are auto-authenticated as username USR; example: [172.16.24.0/24=dave] (default: None)"),
    new Argument("--ipr", "REPEATABLE: username USR can only connect from an IP matching one or more CIDR (comma-sep.); example: [192.168.123.0/24,172.16.0.0/16=dave] (default: None)"),
    new Argument("--chpw", "allow users to change their own passwords (default: False)"),
    new Argument("--chpw-no", "REPEATABLE: do not allow password-changes for this comma-separated list of usernames (default: None)"),
    new Argument("--chpw-db", "where to store the passwords database (if you run multiple copyparty instances, make sure they use different DBs) (default: ~/.config/copyparty/chpw.json)"),
    new Argument("--chpw-len", "minimum password length (default: 8)"),
    new Argument("--chpw-v", "verbosity of summary on config load [0] = nothing at all, [1] = number of users, [2] = list users with default-pw, [3] = list all users (default: 2)"),
    new Argument("--qr", "show QR-code on startup (default: False)"),
    new Argument("--qrs", "change the QR-code URL to https:// (default: False)"),
    new Argument("--qrl", "location to include in the url, for example [priv/?pw=hunter2] (default: )"),
    new Argument("--qri", "select IP which starts with PREFIX; [.] to force default IP when mDNS URL would have been used instead (default: )"),
    new Argument("--qr-fg", "foreground; try [0] or [-1] if the qr-code is unreadable (default: 16)"),
    new Argument("--qr-bg", "background (white=255) (default: 229)"),
    new Argument("--qrp", "padding (spec says 4 or more, but 1 is usually fine) (default: 4)"),
    new Argument("--qrz", "[1]=1x, [2]=2x, [0]=auto (try [2] on broken fonts) (default: 0)"),
    new Argument("--qr-pin", "sticky/pin the qr-code to always stay on-screen; [0]=disabled, [1]=with-url, [2]=just-qr (default: 0)"),
    new Argument("--qr-wait", "wait SEC before printing the qr-code to the log (default: 0)"),
    new Argument("--qr-every", "print the qr-code every SEC (try this with/without --qr-pin in case of issues) (default: 0)"),
    new Argument("--qr-winch", "when --qr-pin is enabled, check for terminal size change every SEC (default: 0)"),
    new Argument("--qr-file", "REPEATABLE: write qr-code to file. └─To create txt or svg, TXT is Filepath:Zoom:Pad, for example [qr.txt:1:2] └─To create png or gif, TXT is Filepath:Zoom:Pad:Foreground:Background, for example [qr.png:8:2:333333:ffcc55], or  [qr.png:8:2::ffcc55] for transparent (default: None)"),
    new Argument("--qr-stdout", "always display the QR-code on STDOUT in the terminal, even if -q (default: False)"),
    new Argument("--qr-stderr", "always display the QR-code on STDERR in the terminal, even if -q (default: False)"),
    new Argument("-z", "enable all zeroconf backends (mdns, ssdp) (default: False)"),
    new Argument("--z-on", "enable zeroconf ONLY on the comma-separated list of subnets and/or interface names/indexes └─example: eth0, wlo1, virhost0, 192.168.123.0/24, fd00:fda::/96 (default: )"),
    new Argument("--z-off", "disable zeroconf on the comma-separated list of subnets and/or interface names/indexes (default: )"),
    new Argument("--z-chk", "check for network changes every SEC seconds (0=disable) (default: 10)"),
    new Argument("-zv", "verbose all zeroconf backends (default: False)"),
    new Argument("--mc-hop", "rejoin multicast groups every SEC seconds (workaround for some switches/routers which cause mDNS to suddenly stop working after some time); try [300] or [180] └─note: can be due to firewalls; make sure UDP port 5353 is open in both directions (on clients too) (default: 0)"),
    new Argument("--zm", "announce the enabled protocols over mDNS (multicast DNS-SD) -- compatible with KDE, gnome, macOS, ... (default: False)"),
    new Argument("--zm-on", "enable mDNS ONLY on the comma-separated list of subnets and/or interface names/indexes (default: )"),
    new Argument("--zm-off", "disable mDNS on the comma-separated list of subnets and/or interface names/indexes (default: )"),
    new Argument("--zm4", "IPv4 only -- try this if some clients can't connect (default: False)"),
    new Argument("--zm6", "IPv6 only (default: False)"),
    new Argument("--zmv", "verbose mdns (default: False)"),
    new Argument("--zmvv", "verboser mdns (default: False)"),
    new Argument("--zm-http", "port to announce for http/webdav; [-1] = auto, [0] = disabled, [4649] = port 4649 (default: -1)"),
    new Argument("--zm-https", "port to announce for https/webdavs; [-1] = auto, [0] = disabled, [4649] = port 4649 (default: -1)"),
    new Argument("--zm-no-pe", "mute parser errors (invalid incoming MDNS packets) (default: False)"),
    new Argument("--zm-nwa-1", "disable workaround for avahi-bug #379 (corruption in Avahi's mDNS reflection feature) (default: False)"),
    new Argument("--zms", "list of services to announce -- d=webdav h=http f=ftp s=smb -- lowercase=plaintext uppercase=TLS -- default: all enabled services except http/https (Ddfs if --ftp and --smb is set, Dd otherwise) (default: )"),
    new Argument("--zm-ld", "link a specific folder for webdav shares (default: )"),
    new Argument("--zm-lh", "link a specific folder for http shares (default: )"),
    new Argument("--zm-lf", "link a specific folder for ftp shares (default: )"),
    new Argument("--zm-ls", "link a specific folder for smb shares (default: )"),
    new Argument("--zm-fqdn", "the domain to announce; NOTE: using anything other than .local is nonstandard and could cause problems (default: --name.local)"),
    new Argument("--zm-mnic", "merge NICs which share subnets; assume that same subnet means same network (default: False)"),
    new Argument("--zm-msub", "merge subnets on each NIC -- always enabled for ipv6 -- reduces network load, but gnome-gvfs clients may stop working, and clients cannot be in subnets that the server is not (default: False)"),
    new Argument("--zm-noneg", "disable NSEC replies -- try this if some clients don't see copyparty (default: False)"),
    new Argument("--zm-spam", "send unsolicited announce every SEC; useful if clients have IPs in a subnet which doesn't overlap with the server, or to avoid some firewall issues (default: 0.0)"),
    new Argument("--zs", "announce the enabled protocols over SSDP -- compatible with Windows (default: False)"),
    new Argument("--zs-on", "enable SSDP ONLY on the comma-separated list of subnets and/or interface names/indexes (default: )"),
    new Argument("--zs-off", "disable SSDP on the comma-separated list of subnets and/or interface names/indexes (default: )"),
    new Argument("--zsv", "verbose SSDP (default: False)"),
    new Argument("--zsl", "location to include in the url (or a complete external URL), for example [priv/?pw=hunter2] (goes directly to /priv/ with password hunter2) or [?hc=priv&pw=hunter2] (shows mounting options for /priv/ with password) (default: /?hc)"),
    new Argument("--zsid", "USN (device identifier) to announce (default: autogenerated)"),
    new Argument("--casechk", "detect and prevent CI (case-insensitive) behavior if the underlying filesystem is CI? [y] = detect and prevent, [n] = ignore and allow, [auto] = y if CI fs detected. NOTE: y is very slow but necessary for correct WebDAV behavior on Windows/Macos (volflag=casechk) (default: auto)"),
    new Argument("--fsnt", "which characters to allow in file/folder names; [win] = windows (not <>:|?*\"\\/), [mac] = macos (not :), [lin] = linux (anything goes) (volflag=fsnt) (default: auto)"),
    new Argument("--rm-retry", "if a file cannot be deleted because it is busy, continue trying for T seconds, retry every R seconds; disable with 0/0 (volflag=rm_retry) (default: 0/0)"),
    new Argument("--mv-retry", "if a file cannot be renamed because it is busy, continue trying for T seconds, retry every R seconds; disable with 0/0 (volflag=mv_retry) (default: 0/0)"),
    new Argument("--iobuf", "file I/O buffer-size; if your volumes are on a network drive, try increasing to 524288 or even 4194304 (and let me know if that improves your performance) (default: 262144)"),
    new Argument("--mtab-age", "rebuild mountpoint cache every SEC to keep track of sparse-files support; keep low on servers with removable media (default: 60)"),
    new Argument("--shr", "toplevel virtual folder for shared files/folders, for example [/share] (default: )"),
    new Argument("--shr-db", "database to store shares in (default: ~/.config/copyparty/shares.db)"),
    new Argument("--shr-who", "who can create a share? [no]=nobody, [a]=admin-permission, [auth]=authenticated (volflag=shr_who) (default: auth)"),
    new Argument("--shr-adm", "comma-separated list of users allowed to view/delete any share (default: )"),
    new Argument("--shr-rt", "shares can be revived by their owner if they expired less than MIN minutes ago; [60]=hour, [1440]=day, [10080]=week (default: 1440)"),
    new Argument("--shr-site", "public URL to assume when creating share-links; example: [https://example.com/] (default: --site)"),
    new Argument("--shr-v", "debug (default: False)"),
    new Argument("--dotpart", "dotfile incomplete uploads, hiding them from clients unless -ed (default: False)"),
    new Argument("--plain-ip", "when avoiding filename collisions by appending the uploader's ip to the filename: append the plaintext ip instead of salting and hashing the ip (default: False)"),
    new Argument("--up-site", "public URL to assume when creating links to uploaded files; example: [https://example.com/] (default: --site)"),
    new Argument("--put-name", "filename for nameless uploads (when uploader doesn't provide a name); default is [put-UNIXTIME-IP.bin] (the .6f means six decimal places) (volflag=put_name) (default: put-{now.6f}-{cip}.bin)"),
    new Argument("--put-ck", "default checksum-hasher for PUT/WebDAV uploads: no / md5 / sha1 / sha256 / sha512 / b2 / blake2 / b2s / blake2s (volflag=put_ck) (default: sha512)"),
    new Argument("--bup-ck", "default checksum-hasher for bup/basic-uploader: no / md5 / sha1 / sha256 / sha512 / b2 / blake2 / b2s / blake2s (volflag=bup_ck) (default: sha512)"),
    new Argument("--unpost", "grace period where uploads can be deleted by the uploader, even without delete permissions; 0=disabled, default=12h (default: 43200)"),
    new Argument("--unp-who", "clients can undo recent uploads by using the unpost tab (requires -e2d). [0] = never allowed (disable feature), [1] = allow if client has the same IP as the upload AND is using the same account, [2] = just check the IP, [3] = just check account-name (volflag=unp_who) (default: 1)"),
    new Argument("--apnd-who", "who can append to existing files? [no]=nobody, [aw]=admin+write, [dw]=delete+write, [w]=write (volflag=apnd_who) (default: dw)"),
    new Argument("--u2abort", "clients can abort incomplete uploads by using the unpost tab (requires -e2d). [0] = never allowed (disable feature), [1] = allow if client has the same IP as the upload AND is using the same account, [2] = just check the IP, [3] = just check account-name (volflag=u2abort) (default: 1)"),
    new Argument("--blank-wt", "file write grace period (any client can write to a blank file last-modified more recently than SEC seconds ago) (default: 300)"),
    new Argument("--reg-cap", "max number of uploads to keep in memory when running without -e2d; roughly 1 MiB RAM per 600 (default: 38400)"),
    new Argument("--no-fpool", "disable file-handle pooling -- instead, repeatedly close and reopen files during upload (bad idea to enable this on windows and/or cow filesystems) (default: False)"),
    new Argument("--use-fpool", "force file-handle pooling, even when it might be dangerous (multiprocessing, filesystems lacking sparse-files support, ...) (default: False)"),
    new Argument("--chmod-f", "unix file permissions to use when creating files; default is probably 644 (OS-decided), see --help-chmod. Examples: [644] = owner-RW + all-R, [755] = owner-RWX + all-RX, [777] = full-yolo (volflag=chmod_f) (default: )"),
    new Argument("--chmod-d", "unix file permissions to use when creating directories; see --help-chmod. Examples: [755] = owner-RW + all-R, [2750] = setgid + owner-RW + group-R, [777] = full-yolo (volflag=chmod_d) (default: 755)"),
    new Argument("--uid", "unix user-id to chown new files/folders to; default = -1 = do-not-change (volflag=uid) (default: -1)"),
    new Argument("--gid", "unix group-id to chown new files/folders to; default = -1 = do-not-change (volflag=gid) (default: -1)"),
    new Argument("--wram", "allow uploading even if a volume is inside a ramdisk, meaning that all data will be lost on the next server reboot (volflag=wram) (default: False)"),
    new Argument("--dedup", "enable symlink-based upload deduplication (volflag=dedup) (default: False)"),
    new Argument("--safe-dedup", "how careful to be when deduplicating files; [1] = just verify the filesize, [50] = verify file contents have not been altered (volflag=safededup) (default: 50)"),
    new Argument("--hardlink", "enable hardlink-based dedup; will fallback on symlinks when that is impossible (across filesystems) (volflag=hardlink) (default: False)"),
    new Argument("--hardlink-only", "do not fallback to symlinks when a hardlink cannot be made (volflag=hardlinkonly) (default: False)"),
    new Argument("--reflink", "enable reflink-based dedup; will fallback on full copies when that is impossible (non-CoW filesystem) (volflag=reflink) (default: False)"),
    new Argument("--no-dupe", "reject duplicate files during upload; only matches within the same volume (volflag=nodupe) (default: False)"),
    new Argument("--no-dupe-m", "also reject dupes when moving a file into another volume (volflag=nodupem) (default: False)"),
    new Argument("--no-clone", "do not use existing data on disk to satisfy dupe uploads; reduces server HDD reads in exchange for much more network load (volflag=noclone) (default: False)"),
    new Argument("--no-snap", "disable snapshots -- forget unfinished uploads on shutdown; don't create .hist/up2k.snap files -- abandoned/interrupted uploads must be cleaned up manually (default: False)"),
    new Argument("--snap-wri", "write upload state to ./hist/up2k.snap every SEC seconds; allows resuming incomplete uploads after a server crash (default: 300)"),
    new Argument("--snap-drop", "forget unfinished uploads after MIN minutes; impossible to resume them after that (360=6h, 1440=24h) (default: 1440.0)"),
    new Argument("--rm-partial", "delete the .PARTIAL file when an unfinished upload expires after --snap-drop (volflag=rm_partial) (default: False)"),
    new Argument("--u2ts", "how to timestamp uploaded files; [c]=client-last-modified, [u]=upload-time, [fc]=force-c, [fu]=force-u (volflag=u2ts) (default: c)"),
    new Argument("--rotf-tz", "default timezone for the rotf upload rule; examples: [Europe/Oslo], [America/Toronto], [Antarctica/South_Pole] (volflag=rotf_tz) (default: UTC)"),
    new Argument("--rand", "force randomized filenames, --nrand chars long (volflag=rand) (default: False)"),
    new Argument("--nrand", "randomized filenames length (volflag=nrand) (default: 9)"),
    new Argument("--magic", "enable filetype detection on nameless uploads (volflag=magic) (default: False)"),
    new Argument("--df", "ensure GiB free disk space by rejecting upload requests; assumes gigabytes unless a unit suffix is given: [256m], [4], [2T] (volflag=df) (default: 0)"),
    new Argument("--sparse", "windows-only: minimum size of incoming uploads through up2k before they are made into sparse files (default: 4)"),
    new Argument("--turbo", "configure turbo-mode in up2k client; [-1] = forbidden/always-off, [0] = default-off and warn if enabled, [1] = default-off, [2] = on, [3] = on and disable datecheck (default: 0)"),
    new Argument("--nosubtle", "when to use a wasm-hasher instead of the browser's builtin; faster on chrome, but buggy in older chrome versions. [0] = only when necessary (non-https), [1] = always (all browsers), [2] = always on chrome/firefox, [3] = always on chrome, [N] = chrome-version N and newer (recommendation: 137) (default: 0)"),
    new Argument("--u2j", "web-client: number of file chunks to upload in parallel; 1 or 2 is good when latency is low (same-country), 2~4 for android-clients, 2~6 for cross-atlantic. Max is 6 in most browsers. Big values increase network-speed but may reduce HDD-speed (default: 2)"),
    new Argument("--u2sz", "web-client: default upload chunksize (MiB); sets min,default,max in the settings gui. Each HTTP POST will aim for default, and never exceed max. Cloudflare max is 96. Big values are good for cross-atlantic but may increase HDD fragmentation on some FS. Disable this optimization with [1,1,1] (default: 1,64,96)"),
    new Argument("--u2ow", "web-client: default setting for when to replace/overwrite existing files; [0]=never, [1]=if-client-newer, [2]=always (volflag=u2ow) (default: 0)"),
    new Argument("--u2sort", "upload order; [s]=smallest-first, [n]=alphabetical, [fs]=force-s, [fn]=force-n -- alphabetical is a bit slower on fiber/LAN but makes it easier to eyeball if everything went fine (default: s)"),
    new Argument("--write-uplog", "write POST reports to textfiles in working-directory (default: False)"),
    new Argument("-e2d", "enable up2k database; this enables file search, upload-undo, improves deduplication (default: False)"),
    new Argument("-e2ds", "scan writable folders for new files on startup; sets -e2d (default: False)"),
    new Argument("-e2dsa", "scans all folders on startup; sets -e2ds (default: False)"),
    new Argument("-e2v", "verify file integrity; rehash all files and compare with db (default: False)"),
    new Argument("-e2vu", "on hash mismatch: update the database with the new hash (default: False)"),
    new Argument("-e2vp", "on hash mismatch: panic and quit copyparty (default: False)"),
    new Argument("--hist", "where to store volume data (db, thumbs); default is a folder named \".hist\" inside each volume (volflag=hist) (default: )"),
    new Argument("--dbpath", "override where the volume databases are to be placed; default is the same as --hist (volflag=dbpath) (default: )"),
    new Argument("--fika", "list of user-actions to allow while filesystem-indexer is still busy; set blank to never interrupt indexing (old default). [u]=uploads, [c]=filecopy, [m]=move/rename, [d]=delete. NOTE: [m] is untested/scary, and blank is recommended if dedup enabled (default: ucd)"),
    new Argument("--no-hash", "regex: disable hashing of matching absolute-filesystem-paths during e2ds folder scans (must be specified as one big regex, not multiple times) (volflag=nohash) (default: )"),
    new Argument("--no-idx", "regex: disable indexing of matching absolute-filesystem-paths during e2ds folder scan (must be specified as one big regex, not multiple times) (volflag=noidx) (default: )"),
    new Argument("--no-dirsz", "do not show total recursive size of folders in listings, show inode size instead; slightly faster (volflag=nodirsz) (default: False)"),
    new Argument("--re-dirsz", "if the directory-sizes in the UI are bonkers, use this along with -e2dsa to rebuild the index from scratch (default: False)"),
    new Argument("--no-dhash", "disable rescan acceleration; do full database integrity check -- makes the db ~5% smaller and bootup/rescans 3~10x slower (default: False)"),
    new Argument("--re-dhash", "force a cache rebuild on startup; enable this once if it gets out of sync (should never be necessary) (default: False)"),
    new Argument("--no-forget", "never forget indexed files, even when deleted from disk -- makes it impossible to ever upload the same file twice -- only useful for offloading uploads to a cloud service or something (volflag=noforget) (default: False)"),
    new Argument("--forget-ip", "remove uploader-IP from database (and make unpost impossible) MIN minutes after upload, for GDPR reasons. Default [0] is never-forget. [1440]=day, [10080]=week, [43200]=month. (volflag=forget_ip) (default: 0)"),
    new Argument("--dbd", "database durability profile; sets the tradeoff between robustness and speed, see --help-dbd (volflag=dbd) (default: wal)"),
    new Argument("--xlink", "on upload: check all volumes for dupes, not just the target volume (probably buggy, not recommended) (volflag=xlink) (default: False)"),
    new Argument("--hash-mt", "num cpu cores to use for file hashing; set 0 or 1 for single-core hashing (default: numCores if 5 or less)"),
    new Argument("--re-maxage", "rescan filesystem for changes every SEC seconds; 0=off (volflag=scan) (default: 0)"),
    new Argument("--db-act", "defer any scheduled volume reindexing until SEC seconds after last db write (uploads, renames, ...) (default: 10.0)"),
    new Argument("--srch-icase", "case-insensitive search for all unicode characters (the default is icase for just ascii). NOTE: will make searches much slower (around 4x), and NOTE: only applies to filenames/paths, not tags (default: False)"),
    new Argument("--srch-time", "search deadline -- terminate searches running for more than SEC seconds (default: 45)"),
    new Argument("--srch-hits", "max search results to allow clients to fetch; 125 results will be shown initially (default: 7999)"),
    new Argument("--srch-excl", "regex: exclude files from search results if the file-URL matches PTN (case-sensitive). Example: [password|logs/[0-9]] any URL containing 'password' or 'logs/DIGIT' (volflag=srch_excl) (default: )"),
    new Argument("--dotsrch", "show dotfiles in search results (volflags: dotsrch | nodotsrch) (default: False)"),
    new Argument("-e2t", "enable metadata indexing; makes it possible to search for artist/title/codec/resolution/... (default: False)"),
    new Argument("-e2ts", "scan newly discovered files for metadata on startup; sets -e2t (default: False)"),
    new Argument("-e2tsr", "delete all metadata from DB and do a full rescan; sets -e2ts (default: False)"),
    new Argument("--no-mutagen", "use FFprobe for tags instead; will detect more tags (default: False)"),
    new Argument("--no-mtag-ff", "never use FFprobe as tag reader; is probably safer (default: False)"),
    new Argument("--mtag-to", "timeout for FFprobe tag-scan (default: 60)"),
    new Argument("--mtag-mt", "num cpu cores to use for tag scanning (default: numCores)"),
    new Argument("--mtag-v", "verbose tag scanning; print errors from mtp subprocesses and such (default: False)"),
    new Argument("--mtag-vv", "debug mtp settings and mutagen/FFprobe parsers (default: False)"),
    new Argument("--db-xattr", "read file xattrs as metadata tags; [a,b] reads keys a and b as tags a and b, [a=foo,b=bar] reads keys a and b as tags foo and bar, [~~a,b] does everything except a and b, [~~] does everything. NOTE: Each tag must also be enabled with -mte (volflag=db_xattr) (default: )"),
    new Argument("-mtm", "REPEATABLE: add/replace metadata mapping (default: None)"),
    new Argument("-mte", "tags to index/display (comma-sep.); either an entire replacement list, or add/remove stuff on the default-list with +foo or /bar (default: .files,circle,album,.tn,artist,title,tdate,.bpm,key,.dur,.q,.vq,.aq,vc,ac,fmt,res,.fps,ahash, vhash)"),
    new Argument("-mth", "tags to hide by default (comma-sep.); assign/add/remove same as -mte (default: tdate,.vq,.aq,vc,ac,fmt,res,.fps)"),
    new Argument("-mtp", "REPEATABLE: read tag M using program BIN to parse the file (default: None)"),
    new Argument("--no-thumb", "disable all thumbnails (volflag=dthumb) (default: False)"),
    new Argument("--no-vthumb", "disable video thumbnails (volflag=dvthumb) (default: False)"),
    new Argument("--no-athumb", "disable audio thumbnails (spectrograms) (volflag=dathumb) (default: False)"),
    new Argument("--th-size", "thumbnail res (volflag=thsize) (default: 320x256)"),
    new Argument("--th-mt", "num cpu cores to use for generating thumbnails (default: numCores)"),
    new Argument("--th-convt", "convert-to-image timeout in seconds (volflag=convt) (default: 60.0)"),
    new Argument("--ac-convt", "convert-to-audio timeout in seconds (volflag=aconvt) (default: 150.0)"),
    new Argument("--th-ram-max", "max memory usage (GiB) permitted by thumbnailer; not very accurate (default: dynamic)"),
    new Argument("--th-crop", "crop thumbnails to 4:3 or keep dynamic height; client can override in UI unless force. [y]=crop, [n]=nocrop, [fy]=force-y, [fn]=force-n (volflag=crop) (default: y)"),
    new Argument("--th-x3", "show thumbs at 3x resolution; client can override in UI unless force. [y]=yes, [n]=no, [fy]=force-yes, [fn]=force-no (volflag=th3x) (default: n)"),
    new Argument("--th-qv", "webp/jpg thumbnail quality (10~90); higher is larger filesize and better quality (volflag=th_qv) (default: 40)"),
    new Argument("--th-qvx", "jxl thumbnail quality (10~90); higher is larger filesize and better quality (volflag=th_qvx) (default: 64)"),
    new Argument("--th-dec", "image decoders, in order of preference (default: vips,raw,pil,ff)"),
    new Argument("--th-no-jpg", "disable jpg output (default: False)"),
    new Argument("--th-no-webp", "disable webp output (default: False)"),
    new Argument("--th-no-jxl", "disable jpeg-xl output (default: False)"),
    new Argument("--th-ff-jpg", "force jpg output for video thumbs (avoids issues on some FFmpeg builds) (default: False)"),
    new Argument("--th-ff-swr", "use swresample instead of soxr for audio thumbs (faster, lower accuracy, avoids issues on some FFmpeg builds) (default: False)"),
    new Argument("--th-vips-jxl", "when to allow generating jxl thumbnails with libvips; 0=never, 1=musl-mallocng, 2=always (default: 1)"),
    new Argument("--th-poke", "activity labeling cooldown -- avoids doing keepalive pokes (updating the mtime) on thumbnail folders more often than SEC seconds (default: 300)"),
    new Argument("--th-clean", "cleanup interval; 0=disabled (default: 43200)"),
    new Argument("--th-maxage", "max folder age -- folders which haven't been poked for longer than --th-poke seconds will get deleted every --th-clean seconds (default: 604800)"),
    new Argument("--th-pregen", "pregenerate thumbnails on startup; F,F is comma-separated list of formats; example: [j,jf,w,w3,wf,wf3,x,xf] NOTE: remember to set --th-maxage 123456789 (volflag=th_pregen) (default: )"),
    new Argument("--th-pre-rl", "while pregen is running, ratelimit the thumbnailer logger to one message every SEC seconds (only works with -j1); set 0 to disable ratelimit (default: 30)"),
    new Argument("--th-covers", "folder thumbnails to stat/look for; enabling -e2d will make these case-insensitive, and try them as dotfiles (.folder.jpg), and also automatically select thumbnails for all folders that contain pics, even if none match this pattern (default: folder.png,folder.jpg,cover.png,cover.jpg)"),
    new Argument("--th-spec-p", "for music, do spectrograms or embedded coverart? [0]=only-art, [1]=prefer-art, [2]=only-spec (default: 1)"),
    new Argument("--th-spec-fl", "generate spectrograms with logarithmic frequency scale instead of linear (default: False)"),
    new Argument("--th-r-pil", "image formats to decode using pillow (default: avif,avifs,blp,bmp,cbz,dcx,dds,dib,emf,eps,epub,fits,flc,fli,fpx,gif, heic,heics,heif,heifs,icns,ico,im,j2p,j2k,jp2,jpeg,jpg,jpx,jxl,pbm,pcx,pgm,png,pnm,ppm,psd,qoi,sgi,spi,tga,tif,tiff, webp,wmf,xbm,xpm)"),
    new Argument("--th-r-vips", "image formats to decode using pyvips (default: 3fr,arw,avif,cr2,cr3,crw,dcr,dng,erf,exr,fit,fits,fts,gif,hdr,heic, heics,heif,heifs,jp2,jpeg,jpg,jpx,jxl,k25,kdc,mdc,mef,mrw,nef,nii,nrw,orf,pfm,pgm,png,ppm,raf,raw,rw2,sr2,srf,srw,svg, tif,tiff,webp,x3f)"),
    new Argument("--th-r-raw", "image formats to decode using rawpy (if available) or libraw's dcraw_emu (default: 3fr,arw,cr2,cr3,crw,dcr,dng,erf,k25, kdc,mdc,mef,mos,mrw,nef,nrw,orf,pef,raf,raw,rw2,sr2,srf,srw,x3f)"),
    new Argument("--th-r-ffi", "image formats to decode using ffmpeg (default: apng,avif,avifs,bmp,cbz,dds,dib,epub,fit,fits,fts,gif,hdr,heic,heics, heif,heifs,icns,ico,jp2,jpeg,jpg,jpx,jxl,pbm,pcx,pfm,pgm,png,pnm,ppm,psd,qoi,sgi,tga,tif,tiff,webp,xbm,xpm)"),
    new Argument("--th-r-ffv", "video formats to decode using ffmpeg (default: 3gp,asf,av1,avc,avi,flv,h264,h265,hevc,m4v,mjpeg,mjpg,mkv,mov,mp4,mpeg, mpeg2,mpegts,mpg,mpg2,mts,nut,ogm,ogv,rm,ts,vob,webm,wmv)"),
    new Argument("--th-r-ffa", "audio formats to decode using ffmpeg (default: aac,ac3,aif,aiff,alac,alaw,amr,apac,ape,au,bcstm,bfstm,brstm,bonk,dfpwm, dts,flac,gsm,ilbc,it,itgz,itxz,itz,m4a,m4b,m4r,mdgz,mdxz,mdz,mka,mo3,mod,mp2,mp3,mpc,mptm,mt2,mulaw,oga,ogg,okt,opus, ra,s3m,s3gz,s3xz,s3z,tak,tta,ulaw,wav,wma,wv,xm,xmgz,xmxz,xmz,xpk)"),
    new Argument("--th-spec-cnv", "audio formats which provoke https://trac.ffmpeg.org/ticket/10797 (huge ram usage for s3xmodit spectrograms) (default: it,itgz,itxz,itz,mdgz,mdxz,mdz,mo3,mod,s3m,s3gz,s3xz,s3z,xm,xmgz,xmxz,xmz,xpk)"),
    new Argument("--au-unpk", "audio/image formats to decompress before passing to ffmpeg (default: mdz=mod.zip, mdgz=mod.gz, mdxz=mod.xz, s3z=s3m.zip, s3gz=s3m.gz, s3xz=s3m.xz, xmz=xm.zip, xmgz=xm.gz, xmxz=xm.xz, itz=it.zip, itgz=it.gz, itxz=it.xz, cbz=jpg.cbz, epub=jpg.epub)"),
    new Argument("--q-opus", "target bitrate for transcoding to opus; set 0 to disable (default: 128)"),
    new Argument("--q-mp3", "target quality for transcoding to mp3, for example [192k] (CBR) or [q0] (CQ/CRF, q0=maxquality, q9=smallest); set 0 to disable (default: q2)"),
    new Argument("--allow-wav", "allow transcoding to wav (lossless, uncompressed) (default: False)"),
    new Argument("--allow-flac", "allow transcoding to flac (lossless, compressed) (default: False)"),
    new Argument("--no-caf", "disable transcoding to caf-opus (affects iOS v12~v17), will use mp3 instead (default: False)"),
    new Argument("--no-owa", "disable transcoding to webm-opus (iOS v18 and later), will use mp3 instead (default: False)"),
    new Argument("--no-acode", "disable audio transcoding (default: False)"),
    new Argument("--no-bacode", "disable batch audio transcoding by folder download (zip/tar) (default: False)"),
    new Argument("--ac-maxage", "delete cached transcode output after SEC seconds (default: 86400)"),
    new Argument("--rss", "enable RSS output (experimental) (volflag=rss) (default: False)"),
    new Argument("--rss-nf", "default number of files to return (url-param 'nf') (default: 250)"),
    new Argument("--rss-fext", "default list of file extensions to include (url-param 'fext'); blank=all (default: )"),
    new Argument("--rss-sort", "default sort order (url-param 'sort'); [m]=last-modified [u]=upload-time [n]=filename [s]=filesize; Uppercase=oldest-first. Note that upload-time is 0 for non-uploaded files (volflag=rss_sort) (default: m)"),
    new Argument("--rss-fmt-t", "title format (url-param 'rss_fmt_t') (volflag=rss_fmt_t) (default: {fname})"),
    new Argument("--rss-fmt-d", "description format (url-param 'rss_fmt_d') (volflag=rss_fmt_d) (default: {artist} - {title})"),
    new Argument("--sftp", "enable SFTP server on PORT, for example 3922 (default: 0)"),
    new Argument("--sftpv", "verbose (default: False)"),
    new Argument("--sftpvv", "verboser (default: False)"),
    new Argument("--sftp-i", "IPs to listen on (comma-separated list). Set this to override -i for this protocol (default: -i)"),
    new Argument("--sftp4", "only listen on IPv4 (default: False)"),
    new Argument("--sftp-key", "REPEATABLE: add ssh-key K for user U (username, space, key-type, space, base64); if user has multiple keys, then repeat this option for each key └─commandline example: --sftp-key 'david ssh-ed25519 AAAAC3NzaC...' └─config-file example: sftp-key: david ssh-ed25519 AAAAC3NzaC... (default: None)"),
    new Argument("--sftp-pw", "allow password-authentication with sftp (not just ssh-keys) (default: False)"),
    new Argument("--sftp-anon", "allow anonymous/unauthenticated connections with TXT as username (default: )"),
    new Argument("--sftp-hostk", "path to folder with hostkeys, for example 'ssh_host_rsa_key'; missing keys will be generated (default: ~/.config/copyparty)"),
    new Argument("--sftp-banner", "bannertext to send when someone connects; can be @filepath (default: )"),
    new Argument("--sftp-ipa", "only accept connections from IP-addresses inside CIDR (comma-separated); specify [any] to disable inheriting --ipa / --ipar. Examples: [lan] or [10.89.0.0/16, 192.168.33.0/24] (default: )"),
    new Argument("--ftp", "enable FTP server on PORT, for example 3921 (default: 0)"),
    new Argument("--ftps", "enable FTPS server on PORT, for example 3990 (default: 0)"),
    new Argument("--ftpv", "verbose (default: False)"),
    new Argument("--ftp-i", "IPs to listen on (comma-separated list). Set this to override -i for this protocol (default: -i)"),
    new Argument("--ftp4", "only listen on IPv4 (default: False)"),
    new Argument("--ftp-ipa", "only accept connections from IP-addresses inside CIDR (comma-separated); specify [any] to disable inheriting --ipa / --ipar. Examples: [lan] or [10.89.0.0/16, 192.168.33.0/24] (default: )"),
    new Argument("--ftp-no-ow", "if target file exists, reject upload instead of overwrite (default: False)"),
    new Argument("--ftp-wt", "grace period for resuming interrupted uploads (any client can write to any file last-modified more recently than SEC seconds ago) (default: 7)"),
    new Argument("--ftp-nat", "the NAT address to use for passive connections (default: )"),
    new Argument("--ftp-pr", "the range of TCP ports to use for passive connections, for example 12000-13000 (default: )"),
    new Argument("--daw", "enable full write support, even if client may not be webdav. Some webdav clients need this option for editing existing files; not necessary for clients that send the 'x-oc-mtime' header. Regardless, the delete-permission must always be given. WARNING: This has side-effects -- PUT-operations will now OVERWRITE existing files, rather than inventing new filenames to avoid loss of data. You might want to instead set this as a volflag where needed. By not setting this flag, uploaded files can get written to a filename which the client does not expect (which might be okay, depending on client) (default: False)"),
    new Argument("--dav-inf", "allow depth:infinite requests (recursive file listing); extremely server-heavy but required for spec compliance -- luckily few clients rely on this (default: False)"),
    new Argument("--dav-mac", "disable apple-garbage filter -- allow macos to create junk files (._* and .DS_Store, .Spotlight-*, .fseventsd, .Trashes, .AppleDouble, __MACOS) (default: False)"),
    new Argument("--dav-rt", "show symlink-destination's lastmodified instead of the link itself; always enabled for recursive listings (volflag=davrt) (default: False)"),
    new Argument("--dav-auth", "force auth for all folders (required by davfs2 when only some folders are world-readable) (volflag=davauth) (default: False)"),
    new Argument("--dav-ua1", "regex of user-agents which ARE webdav-clients, and expect 401 from GET requests; disable with [no] or blank (default: kioworker/)"),
    new Argument("--dav-port", "additional port to listen on for misbehaving webdav clients which pretend they are graphical browsers; an alternative/supplement to dav-ua1 (default: 0)"),
    new Argument("--ua-nodav", "regex of user-agents which are NOT webdav-clients (default: ^(Mozilla/|NetworkingExtension/|com\\.apple\\.WebKit))"),
    new Argument("--p-nodav", "server-ports (comma-sep.) which are NOT webdav-clients; an alternative/supplement to ua-nodav (default: )"),
    new Argument("--tftp", "enable TFTP server on PORT, for example 69 or 3969 (default: 0)"),
    new Argument("--tftp-i", "IPs to listen on (comma-separated list). Set this to override -i for this protocol (default: -i)"),
    new Argument("--tftp4", "only listen on IPv4 (default: False)"),
    new Argument("--tftpv", "verbose (default: False)"),
    new Argument("--tftpvv", "verboser (default: False)"),
    new Argument("--tftp-no-fast", "debug: disable optimizations (default: False)"),
    new Argument("--tftp-lsf", "return a directory listing if a file with this name is requested and it does not exist; defaults matches .ls, dir, .dir.txt, ls.txt, ... (default: \\.?(dir|ls)(\\.txt)?)"),
    new Argument("--tftp-nols", "if someone tries to download a directory, return an error instead of showing its directory listing (default: False)"),
    new Argument("--tftp-ipa", "only accept connections from IP-addresses inside CIDR (comma-separated); specify [any] to disable inheriting --ipa / --ipar. Examples: [lan] or [10.89.0.0/16, 192.168.33.0/24] (default: )"),
    new Argument("--tftp-pr", "the range of UDP ports to use for data transfer, for example 12000-13000 (default: )"),
    new Argument("--smb", "enable smb (read-only) -- this requires running copyparty as root on linux and macos unless --smb-port is set above 1024 and your OS does port-forwarding from 445 to that.WARNING: this protocol is DANGEROUS and buggy! Never expose to the internet! (default: False)"),
    new Argument("--smb-i", "IPs to listen on (comma-separated list). Set this to override -i for this protocol (default: -i)"),
    new Argument("--smbw", "enable write support (please dont) (default: False)"),
    new Argument("--smb1", "disable SMBv2, only enable SMBv1 (CIFS) (default: False)"),
    new Argument("--smb-port", "port to listen on -- if you change this value, you must NAT from TCP:445 to this port using iptables or similar (default: 445)"),
    new Argument("--smb-nwa-1", "truncate directory listings to 64kB (~400 files); avoids impacket-0.11 bug, fixes impacket-0.12 performance (default: False)"),
    new Argument("--smb-nwa-2", "disable impacket workaround for filecopy globs (default: False)"),
    new Argument("--smba", "small performance boost: disable per-account permissions, enables account coalescing instead (if one user has write/delete-access, then everyone does) (default: False)"),
    new Argument("--smb6", "enable IPv6 (default: False)"),
    new Argument("--smbv", "verbose (default: False)"),
    new Argument("--smbvv", "verboser (default: False)"),
    new Argument("--smbvvv", "verbosest (default: False)"),
    new Argument("--opds", "enable opds -- allows e-book readers to browse and download files (volflag=opds) (default: False)"),
    new Argument("--opds-exts", "file formats to list in OPDS feeds; leave empty to show everything (volflag=opds_exts) (default: epub,cbz,pdf)"),
    new Argument("-s", "increase safety: Disable thumbnails / potentially dangerous software (ffmpeg/pillow/vips), hide partial uploads, avoid crawlers. └─Alias of --dotpart --no-thumb --no-mtag-ff --no-robots --force-js (default: 0)"),
    new Argument("-ss", "further increase safety: Prevent js-injection, accidental move/delete, broken symlinks, webdav requires login, 404 on 403, ban on excessive 404s. └─Alias of -s --no-html --no-readme --no-logues --unpost=0 --no-del --no-mv --reflink --dav-auth --vague-403 -nih  (default: False)"),
    new Argument("-sss", "further increase safety: Enable logging to disk, scan for dangerous symlinks. └─Alias of -ss --no-dav --no-logues --no-readme -lo=cpp-%Y-%m%d-%H%M%S.txt.xz --ls=**,*,ln,p,r (default: False)"),
    new Argument("--ls", "do a sanity/safety check of all volumes on startup; new Arguments USER,VOL,FLAGS (see --help-ls); example [**,*,ln,p,r] (default: )"),
    new Argument("--xvol", "never follow symlinks leaving the volume root, unless the link is into another volume where the user also has access (keeps permissions from the outer/initial volume) (volflag=xvol) (default: False)"),
    new Argument("--xdev", "stay within the filesystem of the volume root; do not descend into other devices (symlink or bind-mount to another HDD,  ...) (volflag=xdev) (default: False)"),
    new Argument("--vol-nospawn", "if a volume's folder does not exist on the HDD, then do not create it (continue with warning) (volflag=nospawn) (default: False)"),
    new Argument("--vol-or-crash", "if a volume's folder does not exist on the HDD, then burst into flames (volflag=assert_root) (default: False)"),
    new Argument("--no-dot-mv", "disallow moving dotfiles; makes it impossible to move folders containing dotfiles (default: False)"),
    new Argument("--no-dot-ren", "disallow renaming dotfiles; makes it impossible to turn something into a dotfile (default: False)"),
    new Argument("--no-logues", "disable rendering .prologue/.epilogue.html into directory listings (default: False)"),
    new Argument("--no-readme", "disable rendering readme/preadme.md into directory listings (default: False)"),
    new Argument("--no-script", "disables javascript in html files; helps prevent XSS but kills interactive websites (volflag=noscript) (default: False)"),
    new Argument("--no-html", "show html-files as plain text; helps prevent XSS but kills websites/blogs, also enables --no-script (volflag=nohtml) (default: False)"),
    new Argument("--vague-403", "send 404 instead of 403 (security through ambiguity, very enterprise). WARNING: Not compatible with WebDAV (default: False)"),
    new Argument("--force-js", "don't send folder listings as HTML, force clients to use the embedded json instead -- slight protection against misbehaving search engines which ignore --no-robots (default: False)"),
    new Argument("--no-robots", "adds http and html headers asking search engines to not index anything (volflag=norobots) (default: False)"),
    new Argument("--logout", "logout clients after H hours of inactivity; [0.0028]=10sec, [0.1]=6min, [24]=day, [168]=week, [720]=month, [8760]=year) (default: 8086.0)"),
    new Argument("--dont-ban", "anyone at this accesslevel or above will not get banned: [av]=admin-in-volume, [aa]=has-admin-anywhere, [rw]=read-write, [auth]=authenticated, [any]=disable-all-bans, [no]=anyone-can-get-banned (default: no)"),
    new Argument("--banmsg", "the response to send to banned users; can be @ban.html to send the contents of ban.html (default: thank you for playing   (see fileserver log and readme))"),
    new Argument("--ban-pw", "more than N wrong passwords in W minutes = ban for B minutes; disable with [no] (default: 9,60,1440)"),
    new Argument("--ban-pwc", "more than N password-changes in W minutes = ban for B minutes; disable with [no] (default: 5,60,1440)"),
    new Argument("--ban-404", "hitting more than N 404's in W minutes = ban for B minutes; only affects users who cannot see directory listings because their access is either g/G/h (default: 50,60,1440)"),
    new Argument("--ban-403", "hitting more than N 403's in W minutes = ban for B minutes; [1440]=day, [10080]=week, [43200]=month (default: 9,2,1440)"),
    new Argument("--ban-422", "hitting more than N 422's in W minutes = ban for B minutes (invalid requests, attempted exploits ++) (default: 9,2, 1440)"),
    new Argument("--ban-url", "hitting more than N sus URL's in W minutes = ban for B minutes; applies only to permissions g/G/h (decent replacement for --ban-404 if that can't be used) (default: 9,2,1440)"),
    new Argument("--sus-urls", "URLs which are considered sus / eligible for banning; disable with blank or [no] (default: \\.php\\$|(^|/)wp-(admin|content|includes)/)"),
    new Argument("--nonsus-urls", "harmless URLs ignored from 403/404-bans; disable with blank or [no] (default: ^(favicon\\..{3}|robots\\.txt)\\$|^apple-touch-icon|^\\.well-known)"),
    new Argument("--early-ban", "if a client is banned, reject its connection as soon as possible; not a good idea to enable when proxied behind cloudflare since it could ban your reverse-proxy (default: False)"),
    new Argument("--cookie-nmax", "reject HTTP-request from client if they send more than N cookies (default: 50)"),
    new Argument("--cookie-cmax", "reject HTTP-request from client if more than N characters in Cookie header (default: 8192)"),
    new Argument("--aclose", "if a client maxes out the server connection limit, downgrade it from connection:keep-alive to connection:close for MIN minutes (and also kill its active connections) -- disable with 0 (default: 10)"),
    new Argument("--loris", "if a client maxes out the server connection limit without sending headers, ban it for B minutes; disable with [0] (default: 60)"),
    new Argument("--acao", "Access-Control-Allow-Origin; list of origins (domains/IPs without port) to accept requests from; [https://1.2.3.4]. Default [*] allows requests from all sites but removes cookies and http-auth; only ?pw=hunter2 survives (default: *)"),
    new Argument("--acam", "Access-Control-Allow-Methods; list of methods to accept from offsite ('*' behaves like --acao's description) (default: GET,HEAD)"),
    new Argument("--ah-alg", "account-pw hashing algorithm; one of these, best to worst: argon2 scrypt sha2 none (each optionally followed by alg-specific comma-sep. config) (default: none)"),
    new Argument("--ah-salt", "account-pw salt; ignored if --ah-alg is none (default) (default: 24-character-autogenerated)"),
    new Argument("--ah-gen", "generate hashed password for PW, or read passwords from STDIN if PW is [-] (default: )"),
    new Argument("--ah-cli", "launch an interactive shell which hashes passwords without ever storing or displaying the original passwords (default: False)"),
    new Argument("--fk-salt", "per-file accesskey salt; used to generate unpredictable URLs for hidden files (default: 24-character-autogenerated)"),
    new Argument("--dk-salt", "per-directory accesskey salt; used to generate unpredictable URLs to share folders with users who only have the 'get' permission (default: 40-character-autogenerated)"),
    new Argument("--warksalt", "up2k file-hash salt; serves no purpose, no reason to change this (but delete all databases if you do) (default: hunter2)"),
    new Argument("--show-ah-salt", "on startup, print the effective value of --ah-salt (the autogenerated value in \$XDG_CONFIG_HOME unless otherwise specified) (default: False)"),
    new Argument("--show-fk-salt", "on startup, print the effective value of --fk-salt (the autogenerated value in \$XDG_CONFIG_HOME unless otherwise specified) (default: False)"),
    new Argument("--show-dk-salt", "on startup, print the effective value of --dk-salt (the autogenerated value in \$XDG_CONFIG_HOME unless otherwise specified) (default: False)"),
    new Argument("-nw", "never write anything to disk (debug/benchmark) (default: False)"),
    new Argument("--keep-qem", "do not disable quick-edit-mode on windows (it is disabled to avoid accidental text selection in the terminal window, as this would pause execution) (default: False)"),
    new Argument("--no-dav", "disable webdav support (default: False)"),
    new Argument("--no-del", "disable delete operations (default: False)"),
    new Argument("--no-mv", "disable move/rename operations (default: False)"),
    new Argument("--no-cp", "disable copy operations (default: False)"),
    new Argument("--no-fs-abrt", "disable ability to abort ongoing copy/move (default: False)"),
    new Argument("-nih", "no info hostname -- removes it from the UI corner, but the value of --bname still shows in the browsertab title (default: False)"),
    new Argument("-nid", "no info disk-usage -- don't show in UI. This is the same as --du-who no (default: False)"),
    new Argument("-nb", "no powered-by-copyparty branding in UI (default: False)"),
    new Argument("--smsg", "HTTP-methods to allow ?smsg for; will execute xm hooks like urlform / message-to-serverlog; dangerous example: [GET, POST]. WARNING: The default (POST) is safe, but GET is dangerous; security/CSRF hazard (default: POST)"),
    new Argument("--zipmaxn", "reject download-as-zip if more than N files in total; optionally takes a unit suffix: [256], [9K], [4G] (volflag=zipmaxn) (default: 0)"),
    new Argument("--zipmaxs", "reject download-as-zip if total download size exceeds SZ bytes; optionally takes a unit suffix: [256M], [4G], [2T] (volflag=zipmaxs) (default: 0)"),
    new Argument("--zipmaxt", "custom errormessage when download size exceeds max (volflag=zipmaxt) (default: )"),
    new Argument("--zipmaxu", "authenticated users bypass the zip size limit (volflag=zipmaxu) (default: False)"),
    new Argument("--zip-who", "who can download as zip/tar? [0]=nobody, [1]=admins, [2]=authenticated-with-read-access, [3]=everyone-with-read-access (volflag=zip_who)WARNING: if a nested volume has a more restrictive value than a parent volume, then this will be ignored if the download is initiated from the parent, more lenient volume (default: 3)"),
    new Argument("--ua-nozip", "regex of user-agents to reject from download-as-zip/tar; disable with [no] or blank (default: Barkrowler|bingbot|BLEXBot|Googlebot|GoogleOther|GPTBot|PetalBot|SeekportBot|SemrushBot|YandexBot)"),
    new Argument("--no-zip", "disable download as zip/tar; same as --zip-who=0 (default: False)"),
    new Argument("--no-tarcmp", "disable download as compressed tar (?tar=gz, ?tar=bz2, ?tar=xz, ?tar=gz:9, ...) (default: False)"),
    new Argument("--no-lifetime", "do not allow clients (or server config) to schedule an upload to be deleted after a given time (default: False)"),
    new Argument("--no-pipe", "disable race-the-beam (lockstep download of files which are currently being uploaded) (volflag=nopipe) (default: False)"),
    new Argument("--no-tail", "disable streaming a growing files with ?tail (volflag=notail) (default: False)"),
    new Argument("--no-db-ip", "do not write uploader-IP into the database; will also disable unpost, you may want --forget-ip instead (volflag=no_db_ip) (default: False)"),
    new Argument("--no-zls", "disable browsing the contents of zip/cbz files, does not affect thumbnails (default: False)"),
    new Argument("--ign-ebind", "continue running even if it's impossible to listen on some of the requested endpoints (default: False)"),
    new Argument("--ign-ebind-all", "continue running even if it's impossible to receive connections at all (default: False)"),
    new Argument("--exit", "shutdown after WHEN has finished; [cfg] config parsing, [idx] volscan + multimedia indexing, [thgen] thumbnail-pregen (default: )"),
    new Argument("--allow-csrf", "disable csrf protections; let other domains/sites impersonate you through cross-site requests; DANGEROUS / LAN-only (default: False)"),
    new Argument("--cookie-lax", "allow cookies from other domains (if you follow a link from another website into your server, you will arrive logged-in); this reduces protection against CSRF (default: False)"),
    new Argument("--no-fnugg", "disable the smoketest for caching-related issues in the web-UI (default: False)"),
    new Argument("--getmod", "permit ?move=[...] and ?delete as GET -- DANGEROUS, removes csrf protection (default: False)"),
    new Argument("--wo-up-readme", "allow users with write-only access to upload logues and readmes without adding the _wo_ filename prefix (volflag=wo_up_readme) (default: False)"),
    new Argument("--unsafe-state", "when one of the emergency fallback locations are used for runtime state (\$TMPDIR, /tmp), certain features will be force-disabled for security reasons by default. This option overrides that safeguard and allows unsafe storage of secrets (default: False)"),
    new Argument("--on404", "REPEATABLE: handle 404s by executing PY file (default: None)"),
    new Argument("--on403", "REPEATABLE: handle 403s by executing PY file (default: None)"),
    new Argument("--hot-handlers", "recompile handlers on each request -- expensive but convenient when hacking on stuff (default: False)"),
    new Argument("--xbu", "REPEATABLE: execute CMD before a file upload starts (default: None)"),
    new Argument("--xau", "REPEATABLE: execute CMD after  a file upload finishes (default: None)"),
    new Argument("--xiu", "REPEATABLE: execute CMD after  all uploads finish and volume is idle (default: None)"),
    new Argument("--xbc", "REPEATABLE: execute CMD before a file copy (default: None)"),
    new Argument("--xac", "REPEATABLE: execute CMD after  a file copy (default: None)"),
    new Argument("--xbr", "REPEATABLE: execute CMD before a file move/rename (default: None)"),
    new Argument("--xar", "REPEATABLE: execute CMD after  a file move/rename (default: None)"),
    new Argument("--xbd", "REPEATABLE: execute CMD before a file delete (default: None)"),
    new Argument("--xad", "REPEATABLE: execute CMD after  a file delete (default: None)"),
    new Argument("--xm", "REPEATABLE: execute CMD on message (default: None)"),
    new Argument("--xban", "REPEATABLE: execute CMD if someone gets banned (pw/404/403/url) (default: None)"),
    new Argument("--hook-v", "verbose hooks (default: False)"),
    new Argument("--stats", "enable openmetrics at /.cpr/metrics for admin accounts (default: False)"),
    new Argument("--stats-u", "comma-separated list of users allowed to access /.cpr/metrics even if they aren't admin (default: )"),
    new Argument("--nos-hdd", "disable disk-space metrics (used/free space) (default: False)"),
    new Argument("--nos-vol", "disable volume size metrics (num files, total bytes, vmaxb/vmaxn) (default: False)"),
    new Argument("--nos-vst", "disable volume state metrics (indexing, analyzing, activity) (default: False)"),
    new Argument("--nos-dup", "disable dupe-files metrics (good idea; very slow) (default: False)"),
    new Argument("--nos-unf", "disable unfinished-uploads metrics (default: False)"),
    new Argument("--rw-edit", "comma-sep. list of file-extensions to allow editing with permissions read+write; all others require read+write+delete (volflag=rw_edit) (default: md)"),
    new Argument("--md-no-br", "markdown: disable newline-is-newline; will only render a newline into the html given two trailing spaces or a double-newline (volflag=md_no_br) (default: False)"),
    new Argument("--md-hist", "where to store old version of markdown files; [s]=subfolder, [v]=volume-histpath, [n]=nope/disabled (volflag=md_hist) (default: s)"),
    new Argument("--txt-eol", "enable EOL conversion when writing documents; supported: CRLF, LF (volflag=txt_eol) (default: )"),
    new Argument("-mcr", "the textfile editor will check for serverside changes every SEC seconds (default: 60)"),
    new Argument("-emp", "enable markdown plugins -- neat but dangerous, big XSS risk (default: False)"),
    new Argument("--exp", "enable textfile expansion -- replace {{self.ip}} and such; see --help-exp (volflag=exp) (default: False)"),
    new Argument("--exp-md", "comma/space-separated list of placeholders to expand in markdown files; add/remove stuff on the default list with +hdr_foo or /vf.scan (volflag=exp_md) (default: self.ip self.ua self.uname self.host cfg.name cfg.logout vf.scan vf.thsize hdr.cf-ipcountry srv.itime srv.htime)"),
    new Argument("--exp-lg", "comma/space-separated list of placeholders to expand in prologue/epilogue files (volflag=exp_lg) (default: self.ip self.ua self.uname self.host cfg.name cfg.logout vf.scan vf.thsize hdr.cf-ipcountry srv.itime srv.htime)"),
    new Argument("--ua-nodoc", "regex of user-agents to reject from viewing documents through ?doc=[...]; disable with [no] or blank (default: Barkrowler|bingbot|BLEXBot|Googlebot|GoogleOther|GPTBot|PetalBot|SeekportBot|SemrushBot|YandexBot)"),
    new Argument("--tail-who", "who can tail? [0]=nobody, [1]=admins, [2]=authenticated-with-read-access, [3]=everyone-with-read-access (volflag=tail_who) (default: 2)"),
    new Argument("--tail-cmax", "do not allow starting a new tail if more than N active downloads (default: 64)"),
    new Argument("--tail-tmax", "terminate connection after SEC seconds; [0]=never (volflag=tail_tmax) (default: 0)"),
    new Argument("--tail-rate", "check for new data every SEC seconds (volflag=tail_rate) (default: 0.2)"),
    new Argument("--tail-ka", "send a zerobyte if connection is idle for SEC seconds to prevent disconnect (default: 3.0)"),
    new Argument("--tail-fd", "check if file was replaced (new fd) if idle for SEC seconds (volflag=tail_fd) (default: 1.0)"),
    new Argument("--og", "disable hotlinking and return an html document instead; this is required by open-graph, but can also be useful on its own (volflag=og) (default: False)"),
    new Argument("--og-ua", "only disable hotlinking / engage OG behavior if the useragent matches regex RE (volflag=og_ua) (default: )"),
    new Argument("--og-tpl", "do not return the regular copyparty html, but instead load the jinja2 template at PATH (if path contains 'EXT' then EXT will be replaced with the requested file's extension) (volflag=og_tpl) (default: )"),
    new Argument("--og-no-head", "do not automatically add OG entries into <head> (useful if you're doing this yourself in a template or such) (volflag=og_no_head) (default: False)"),
    new Argument("--og-th", "thumbnail format; j=jpeg, jf=jpeg-uncropped, jf3=jpeg-uncropped-large, w=webm, ... (volflag=og_th) (default: jf3)"),
    new Argument("--og-title", "fallback title if there is nothing in the -e2t database (volflag=og_title) (default: )"),
    new Argument("--og-title-a", "audio title format; takes any metadata key (volflag=og_title_a) (default: 🎵 {{ artist }} - {{ title }})"),
    new Argument("--og-title-v", "video title format; takes any metadata key (volflag=og_title_v) (default: {{ title }})"),
    new Argument("--og-title-i", "image title format; takes any metadata key (volflag=og_title_i) (default: {{ title }})"),
    new Argument("--og-s-title", "force default title; do not read from tags (volflag=og_s_title) (default: False)"),
    new Argument("--og-desc", "description text; same for all files, disable with [-] (volflag=og_desc) (default: )"),
    new Argument("--og-site", "sitename; defaults to --name, disable with [-] (volflag=og_site) (default: )"),
    new Argument("--tcolor", "accent color (3 or 6 hex digits); may also affect safari and/or android-chrome (volflag=tcolor) (default: 333)"),
    new Argument("--uqe", "query-string parceling; translate a request for /foo/.uqe/BASE64 into /foo?TEXT, or /foo/?TEXT if the first character in TEXT is a slash. Automatically enabled for --og (default: False)"),
    new Argument("--grid", "show grid/thumbnails by default (volflag=grid) (default: False)"),
    new Argument("--gsel", "select files in grid by ctrl-click (volflag=gsel) (default: False)"),
    new Argument("--localtime", "default to local timezone instead of UTC (default: False)"),
    new Argument("--ui-filesz", "default filesize format; one of these: 0, 1, 2, 2c, 3, 3c, 4, 4c, 5, 5c, 6, 6c, 7, 7c, fuzzy (see UI) (default: 1)"),
    new Argument("--gauto", "switch to gridview if more than PERCENT of files are pics/vids; 0=disabled (default: 0)"),
    new Argument("--rcm", "rightclick-menu; two yes/no options: 1st y/n is enable-custom-menu, 2nd y/n is enable-double (default: yy)"),
    new Argument("--lang", "language, for example eng / nor / ... (default: eng)"),
    new Argument("--glang", "guess the browser's default language, otherwise fall back to --lang (default: False)"),
    new Argument("--theme", "default theme to use (0..9) (default: 0)"),
    new Argument("--themes", "number of themes installed (default: 10)"),
    new Argument("--au-vol", "default audio/video volume percent (default: 50)"),
    new Argument("--sort", "default sort order, comma-separated column IDs (see header tooltips), prefix with '-' for descending. Examples: href -href ext sz ts tags/Album tags/.tn (volflag=sort) (default: href)"),
    new Argument("--nsort", "default-enable natural sort of filenames with leading numbers (volflag=nsort) (default: False)"),
    new Argument("--hsortn", "number of sorting rules to include in media URLs by default (volflag=hsortn) (default: 2)"),
    new Argument("--see-dots", "default-enable seeing dotfiles; only takes effect if user has the necessary permissions (default: False)"),
    new Argument("--qdel", "number of confirmations to show when deleting files (2/1/0) (default: 2)"),
    new Argument("--dlni", "force download (don't show inline) when files are clicked (volflag:dlni) (default: False)"),
    new Argument("--unlist", "don't show files/folders matching REGEX in file list. WARNING: Purely cosmetic! Does not affect API calls, just the browser. Example: [\\.(js|css)\\$] (volflag=unlist) (default: )"),
    new Argument("--dothidden", "hide specific files in a folder by listing them in a file named .hidden -- WARNING: Mostly cosmetic! Download-as-zip/tar will still download them. Do not rely on this for security (volflag=dothidden) (default: False)"),
    new Argument("--favico", "favicon-text [ foreground [ background ] ], set blank to disable (default: 🎉 000 none)"),
    new Argument("--ufavico", "URL to .ico/png/gif/svg file; --favico takes precedence unless disabled (volflag=ufavico) (default: )"),
    new Argument("--bg-img", "URL to .jpg/png/gif/svg file (volflag=background)"),
    new Argument("--ext-th", "REPEATABLE: use thumbnail-image VP for file-extension E, example: [exe=/.res/exe.png] (volflag=ext_th) (default: None)"),
    new Argument("--notooltips", "tooltips disabled as default (default: False)"),
    new Argument("--spinner", "emoji or emoji,css Example: [🥖,padding:0] (default: 🌲)"),
    new Argument("--css-browser", "URL to additional CSS to include in the filebrowser html (default: )"),
    new Argument("--js-browser", "URL to additional JS to include in the filebrowser html (default: )"),
    new Argument("--js-other", "URL to additional JS to include in all other pages (default: )"),
    new Argument("--html-head", "text to append to the <head> of all HTML pages (except for basic-browser); can be @PATH to send the contents of a file at PATH, and/or begin with % to render as jinja2 template (volflag=html_head) (default: )"),
    new Argument("--html-head-s", "text to append to the <head> of all HTML pages (except for basic-browser); similar to (and can be combined with) --html-head but only accepts static text (volflag=html_head_s) (default: )"),
    new Argument("--ih", "if a folder contains index.html, show that instead of the directory listing by default (can be changed in the client settings UI, or add ?v to URL for override) (default: False)"),
    new Argument("--textfiles", "file extensions to present as plaintext (default: txt,nfo,diz,cue,readme)"),
    new Argument("--txt-max", "max size of embedded textfiles on ?doc= (anything bigger will be lazy-loaded by JS) (default: 64)"),
    new Argument("--prologues", "comma-sep. list of filenames to scan for and use as prologues (embed above/before directory listing) (volflag=prologues) (default: .prologue.html)"),
    new Argument("--epilogues", "comma-sep. list of filenames to scan for and use as epilogues (embed below/after directory listing) (volflag=epilogues) (default: .epilogue.html)"),
    new Argument("--preadmes", "comma-sep. list of filenames to scan for and use as preadmes (embed above/before directory listing) (volflag=preadmes) (default: preadme.md,PREADME.md)"),
    new Argument("--readmes", "comma-sep. list of filenames to scan for and use as readmes (embed below/after directory listing) (volflag=readmes) (default: readme.md,README.md)"),
    new Argument("--doctitle", "title / service-name to show in html documents (default: copyparty @ --name)"),
    new Argument("--bname", "server name (displayed in filebrowser document title) (default: --name)"),
    new Argument("--pb-url", "powered-by link; disable with -nb (default: https://github.com/9001/copyparty)"),
    new Argument("--ver", "show version on the control panel (incompatible with -nb). This is the same as --ver-who all (default: False)"),
    new Argument("--ver-who", "only show version for: [a]=admin-permission-anywhere, [auth]=authenticated, [all]=anyone (default: no)"),
    new Argument("--du-who", "only show disk usage for: [no]=nobody, [a]=admin-permission, [rw]=read-write, [w]=write, [auth]=authenticated, [all]=anyone (volflag=du_who) (default: all)"),
    new Argument("--k304", "configure the option to enable/disable k304 on the controlpanel (workaround for buggy reverse-proxies); [0] = hidden and default-off, [1] = visible and default-off, [2] = visible and default-on (default: 0)"),
    new Argument("--no304", "configure the option to enable/disable no304 on the controlpanel (workaround for buggy caching in browsers); [0] = hidden and default-off, [1] = visible and default-off, [2] = visible and default-on (default: 0)"),
    new Argument("--ctl-re", "the controlpanel Refresh-button will autorefresh every SEC; [0] = just once (default: 1)"),
    new Argument("--md-sbf", "list of capabilities to allow in the iframe 'sandbox' attribute for README.md docs (volflag=md_sbf); see https://developer.mozilla.org/en-US/docs/Web/HTML/Element/iframe#sandbox (default: downloads forms popups scripts top-navigation-by-user-activation)"),
    new Argument("--lg-sbf", "list of capabilities to allow in the iframe 'sandbox' attribute for prologue/epilogue docs (volflag=lg_sbf) (default: downloads forms popups scripts top-navigation-by-user-activation)"),
    new Argument("--md-sba", "the value of the iframe 'allow' attribute for README.md docs, for example [fullscreen] (volflag=md_sba) (default: )"),
    new Argument("--lg-sba", "the value of the iframe 'allow' attribute for prologue/epilogue docs (volflag=lg_sba); see https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Permissions-Policy#iframes (default: )"),
    new Argument("--no-sb-md", "don't sandbox README/PREADME.md documents (volflags: no_sb_md | sb_md) (default: False)"),
    new Argument("--no-sb-lg", "don't sandbox prologue/epilogue docs (volflags: no_sb_lg | sb_lg); enables non-js support (default: False)"),
    new Argument("--ui-nombar", "hide top-menu in the UI (volflag=ui_nombar) (default: False)"),
    new Argument("--ui-noacci", "hide account-info in the UI (volflag=ui_noacci) (default: False)"),
    new Argument("--ui-nosrvi", "hide server-info in the UI (volflag=ui_nosrvi) (default: False)"),
    new Argument("--ui-nonav", "hide navpane+breadcrumbs (volflag=ui_nonav) (default: False)"),
    new Argument("--ui-notree", "hide navpane in the UI (volflag=ui_notree) (default: False)"),
    new Argument("--ui-nocpla", "hide cpanel-link in the UI (volflag=ui_nocpla) (default: False)"),
    new Argument("--ui-nolbar", "hide link-bar in the UI (volflag=ui_nolbar) (default: False)"),
    new Argument("--ui-noctxb", "hide context-buttons in the UI (volflag=ui_noctxb) (default: False)"),
    new Argument("--ui-norepl", "hide repl-button in the UI (volflag=ui_norepl) (default: False)"),
    new Argument("--no-reload", "disable ?reload=cfg (reload users/volumes/volflags from config file) (default: False)"),
    new Argument("--no-rescan", "disable ?scan (volume reindexing) (default: False)"),
    new Argument("--no-stack", "disable ?stack (list all stacks); same as --stack-who=no (default: False)"),
    new Argument("--no-ups-page", "disable ?ru (list of recent uploads) (default: False)"),
    new Argument("--no-up-list", "don't show list of incoming files in controlpanel (default: False)"),
    new Argument("--dl-list", "who can see active downloads in the controlpanel? [0]=nobody, [1]=admins, [2]=everyone (default: 2)"),
    new Argument("--ups-who", "who can see recent uploads on the ?ru page? [0]=nobody, [1]=admins, [2]=everyone (volflag=ups_who) (default: 2)"),
    new Argument("--ups-when", "let everyone see upload timestamps on the ?ru page, not just admins (default: False)"),
    new Argument("--stack-who", "who can see the ?stack page (list of threads)? [no]=nobody, [a]=admins, [rw]=read+write, [all]=everyone (default: a)"),
    new Argument("--stack-v", "verbose ?stack (default: False)"),
    new Argument("-q", "quiet; disable most STDOUT messages (default: False)"),
    new Argument("-lo", "logfile; use .txt for plaintext or .xz for compressed. Example: cpp-%Y-%m%d-%H%M%S.txt.xz (NB: some errors may appear on STDOUT only) (default: )"),
    new Argument("--flo", "log format for -lo; [1]=classic/colors, [2]=no-color (default: 1)"),
    new Argument("--rlo", "logrotate counter format; see --help-rlo (default: .1)"),
    new Argument("--logrot-sig", "immediately logrotate when unix-signal S is received; examples: [SIGHUP], [HUP], [1] (default: )"),
    new Argument("--no-ansi", "disable colors; same as environment-variable NO_COLOR (default: False)"),
    new Argument("--ansi", "force colors; overrides environment-variable NO_COLOR (default: False)"),
    new Argument("--no-logflush", "don't flush the logfile after each write; tiny bit faster (default: False)"),
    new Argument("--no-voldump", "do not list volumes and permissions on startup (default: False)"),
    new Argument("--log-utc", "do not use local timezone; assume the TZ env-var is UTC (tiny bit faster) (default: False)"),
    new Argument("--log-tdec", "timestamp resolution / number of timestamp decimals (default: 3)"),
    new Argument("--log-date", "date-format, for example [%Y-%m-%d] (default is disabled; no date, just HH:MM:SS) (default: )"),
    new Argument("--log-badpwd", "log failed login attempt passwords: 0=terse, 1=plaintext, 2=hashed (default: 2)"),
    new Argument("--log-badxml", "log any invalid XML received from a client (default: False)"),
    new Argument("--log-conn", "debug: print tcp-server msgs (default: False)"),
    new Argument("--log-htp", "debug: print http-server threadpool scaling (default: False)"),
    new Argument("--ihead", "print request HEADER; [*]=all (default: None)"),
    new Argument("--ohead", "print response HEADER; [*]=all (default: None)"),
    new Argument("--lf-url", "dont log URLs matching regex RE (default: ^/\\.cpr/|[?&]th=[xwjp]|/\\.(_|ql_|DS_Store\\$|localized\\$))"),
    new Argument("--scan-st-r", "fs-indexing: wait SEC between each status-message (default: 0.1)"),
    new Argument("--scan-pr-r", "fs-indexing: wait SEC between each 'progress:' message (default: 10)"),
    new Argument("--scan-pr-s", "fs-indexing: say 'file: <name>' when a file larger than MiB is about to be hashed (default: 1)"),
    new Argument("--vc", "verbose config file parser (explain config) (default: False)"),
    new Argument("--cgen", "generate config file from current config (best-effort; probably buggy) (default: False)"),
    new Argument("--deps", "list information about detected optional dependencies (default: False)"),
    new Argument("--no-poll", "kernel-bug workaround: disable poll; use select instead (limits max num clients to ~700) (default: False)"),
    new Argument("--no-sendfile", "kernel-bug workaround: disable sendfile; do a safe and slow read-send-loop instead (default: False)"),
    new Argument("--no-scandir", "kernel-bug workaround: disable scandir; do a listdir + stat on each file instead (default: False)"),
    new Argument("--no-fastboot", "wait for initial filesystem indexing before accepting client requests (default: False)"),
    new Argument("--no-htp", "disable httpserver threadpool, create threads as-needed instead (default: False)"),
    new Argument("--sig-thr", "start separate thread for OS-signals (try this if CTRL-C is busted) (default: False)"),
    new Argument("--rm-sck", "when listening on unix-sockets, do a basic delete+bind instead of the default atomic bind (default: False)"),
    new Argument("--srch-dbg", "explain search processing, and do some extra expensive sanity checks (default: False)"),
    new Argument("--rclone-mdns", "use mdns-domain instead of server-ip on /?hc (default: False)"),
    new Argument("--stackmon", "write stacktrace to Path every S second, for example --stackmon=./st/%Y-%m/%d/%H%M.xz,60 (default: )"),
    new Argument("--stack-sig", "show stacktrace when unix-signal S is received; examples: [SIGUSR2], [USR2], [12] (default: )"),
    new Argument("--log-thrs", "list active threads every SEC (default: 0.0)"),
    new Argument("--log-fk", "log filekey params for files where path matches REGEX; [.] (a single dot) = all files (default: )"),
    new Argument("--bak-flips", "[up2k] if a client uploads a bitflipped/corrupted chunk, store a copy according to --bf-nc and --bf-dir (default: False)"),
    new Argument("--bf-nc", "bak-flips: stop if there's more than NUM files at --kf-dir already; default: 6.3 GiB max (200*32M) (default: 200)"),
    new Argument("--bf-dir", "bak-flips: store corrupted chunks at PATH; default: folder named 'bf' wherever copyparty was started (default: bf)"),
    new Argument("--bf-log", "bak-flips: log corruption info to a textfile at PATH (default: )"),
    new Argument("--help-bind", "configure listening (default: False)"),
    new Argument("--help-accounts", "accounts and volumes (default: False)"),
    new Argument("--help-auth", "how to login from a client (default: False)"),
    new Argument("--help-auth-ord", "authentication precedence (default: False)"),
    new Argument("--help-flags", "list of volflags (default: False)"),
    new Argument("--help-handlers", "use plugins to handle certain events (default: False)"),
    new Argument("--help-hooks", "execute commands before/after various events (default: False)"),
    new Argument("--help-idp", "replacing the login system with fancy middleware (default: False)"),
    new Argument("--help-urlform", "how to handle url-form POSTs (default: False)"),
    new Argument("--help-exp", "text expansion (default: False)"),
    new Argument("--help-rlo", "logrotate format (default: False)"),
    new Argument("--help-ls", "volume inspection (default: False)"),
    new Argument("--help-dbd", "database durability profiles (default: False)"),
    new Argument("--help-chmod", "file/folder permissions (default: False)"),
    new Argument("--help-pwhash", "password hashing (default: False)"),
    new Argument("--help-zm", "mDNS debugging (default: False)"),
];

// ^\s*([^\s=]+)(?:\s|=)(.*)$
var volflags = [
    new Argument("dedup", "enable symlink-based file deduplication"),
    new Argument("hardlink", "enable hardlink-based file deduplication,with fallback on symlinks when that is impossible"),
    new Argument("hardlinkonly", "dedup with hardlink only, never symlink;make a full copy if hardlink is impossible"),
    new Argument("reflink", "enable reflink-based file deduplication,with fallback on full copy when that is impossible"),
    new Argument("safededup", "verify on-disk data before using it for dedup"),
    new Argument("noclone", "take dupe data from clients, even if available on HDD"),
    new Argument("nodupe", "rejects existing files (instead of linking/cloning them)"),
    new Argument("nodupem", "rejects existing files during moves as well"),
    new Argument("casechk", "auto actively prevent case-insensitive filesystem? y/n"),
    new Argument("chmod_d", "755 unix-permission for new dirs/folders"),
    new Argument("chmod_f", "644 unix-permission for new files"),
    new Argument("uid", "573 change owner of new files/folders to unix-user 573"),
    new Argument("gid", "999 change owner of new files/folders to unix-group 999"),
    new Argument("fsnt", "auto filesystem filename traits (lin/win/mac/auto)"),
    new Argument("wram", "allow uploading into ramdisks"),
    new Argument("sparse", "force use of sparse files, mainly for s3-backed storage"),
    new Argument("nosparse", "deny use of sparse files, mainly for slow storage"),
    new Argument("rm_partial", "delete unfinished uploads from HDD when they timeout"),
    new Argument("daw", "enable full WebDAV write support (dangerous);PUT-operations will now OVERWRITE existing files"),
    new Argument("nosub", "forces all uploads into the top folder of the vfs"),
    new Argument("magic", "enables filetype detection for nameless uploads"),
    new Argument("put_name", "fallback filename for nameless uploads"),
    new Argument("put_ck", "default checksum-hasher for PUT/WebDAV uploads"),
    new Argument("bup_ck", "default checksum-hasher for bup/basic uploads"),
    new Argument("gz", "allows server-side gzip compression of uploads with ?gz"),
    new Argument("xz", "allows server-side lzma compression of uploads with ?xz"),
    new Argument("pk", "forces server-side compression, optional arg: xz,9"),
    new Argument("apnd_who", "dw who can append? (aw/dw/w/no)"),
    new Argument("maxn", "250,600 max 250 uploads over 15min"),
    new Argument("maxb", "1g,300 max 1 GiB over 5min (suffixes: b, k, m, g, t)"),
    new Argument("vmaxb", "1g total volume size max 1 GiB (suffixes: b, k, m, g, t)"),
    new Argument("vmaxn", "4k max 4096 files in volume (suffixes: b, k, m, g, t)"),
    new Argument("medialinks", "return medialinks for non-up2k uploads (not hotlinks)"),
    new Argument("wo_up_readme", "write-only users can upload logues without getting renamed"),
    new Argument("rand", "force randomized filenames, 9 chars long by default"),
    new Argument("nrand", "N randomized filenames are N chars long"),
    new Argument("u2ow", "N overwrite existing files? 0=no 1=if-older 2=always"),
    new Argument("u2ts", "fc [f]orce [c]lient-last-modified or [u]pload-time"),
    new Argument("u2abort", "1 allow aborting unfinished uploads? 0=no 1=strict 2=ip-chk 3=acct-chk"),
    new Argument("sz", "1k-3m allow filesizes between 1 KiB and 3MiB"),
    new Argument("df", "1g ensure 1 GiB free disk space"),
    new Argument("rotn", "100,3 3 levels of subfolders with 100 entries in each"),
    new Argument("rotf", "%Y-%m/%d-%H date-formatted organizing"),
    new Argument("rotf_tz", "Europe/Oslo timezone (default=UTC)"),
    new Argument("lifetime", "3600 uploads are deleted after 1 hour"),
    new Argument("e2d", "enable database; makes files searchable + enables upload-undo"),
    new Argument("e2ds", "scan writable folders for new files on startup; also sets -e2d"),
    new Argument("e2dsa", "scans all folders for new files on startup; also sets -e2d"),
    new Argument("e2t", "enable multimedia indexing; makes it possible to search for tags"),
    new Argument("e2ts", "scan existing files for tags on startup; also sets -e2t"),
    new Argument("e2tsr", "delete all metadata from DB (full rescan); also sets -e2ts"),
    new Argument("d2ts", "disables metadata collection for existing files"),
    new Argument("e2v", "verify integrity on startup by hashing files and comparing to db"),
    new Argument("e2vu", "when e2v fails, update the db (assume on-disk files are good)"),
    new Argument("e2vp", "when e2v fails, panic and quit copyparty"),
    new Argument("d2ds", "disables onboot indexing, overrides -e2ds*"),
    new Argument("d2t", "disables metadata collection, overrides -e2t*"),
    new Argument("d2v", "disables file verification, overrides -e2v*"),
    new Argument("d2d", "disables all database stuff, overrides -e2*"),
    new Argument("hist", "/tmp/cdb puts thumbnails and indexes at that location"),
    new Argument("dbpath", "/tmp/cdb puts indexes at that location"),
    new Argument("landmark", "foo disable db if file foo doesn't exist"),
    new Argument("scan", "60 scan for new files every 60sec, same as --re-maxage"),
    new Argument("nohash", "\\.iso\$ skips hashing file contents if path matches *.iso"),
    new Argument("noidx", "\\.iso\$ fully ignores the contents at paths matching *.iso"),
    new Argument("noforget", "don't forget files when deleted from disk"),
    new Argument("forget_ip", "43200 forget uploader-IP after 30 days (GDPR)"),
    new Argument("no_db_ip", "never store uploader-IP in the db; disables unpost"),
    new Argument("fat32", "avoid excessive reindexing on android sdcardfs"),
    new Argument("dbd", "[acid|swal|wal|yolo] database speed-durability tradeoff"),
    new Argument("xlink", "cross-volume dupe detection / linking (dangerous)"),
    new Argument("xdev", "do not descend into other filesystems"),
    new Argument("xvol", "do not follow symlinks leaving the volume root"),
    new Argument("dotsrch", "show dotfiles in search results"),
    new Argument("nodotsrch", "hide dotfiles in search results (default)"),
    new Argument("srch_excl", "exclude search results with URL matching this regex"),
    new Argument("db_xattr", "user.foo,user.bar index file xattrs as media-tags"),
    new Argument("mte", "artist,title media-tags to index/display"),
    new Argument("mth", "fmt,res,ac media-tags to hide by default"),
    new Argument("mtp", ".bpm=f,audio-bpm.py uses the \"audio-bpm.py\" program togenerate \".bpm\" tags from uploads (f = overwrite tags)"),
    new Argument("mtp", "ahash,vhash=media-hash.py collects two tags at once"),
    new Argument("dthumb", "disables all thumbnails"),
    new Argument("dvthumb", "disables video thumbnails"),
    new Argument("dathumb", "disables audio thumbnails (spectrograms)"),
    new Argument("dithumb", "disables image thumbnails"),
    new Argument("pngquant", "compress audio waveforms 33% better"),
    new Argument("thsize", "thumbnail res; WxH"),
    new Argument("crop", "center-cropping (y/n/fy/fn)"),
    new Argument("th3x", "3x resolution (y/n/fy/fn)"),
    new Argument("th_qv", "40 webp/jpg thumbnail quality (10~90)"),
    new Argument("th_qvx", "40 jxl thumbnail quality (10~90)"),
    new Argument("convt", "convert-to-image timeout in seconds"),
    new Argument("aconvt", "convert-to-audio timeout in seconds"),
    new Argument("th_spec_p", "1 make spectrograms? 0=never 1=fallback 2=always"),
    new Argument("ext_th", "s=/b.png use /b.png as thumbnail for file-extension s"),
    new Argument("th_pregen", "w,wf pregenerate thumbs for these formats"),
    new Argument("on404", "PY handle 404s by executing PY file"),
    new Argument("on403", "PY handle 403s by executing PY file"),
    new Argument("xbu", "CMD execute CMD before a file upload starts"),
    new Argument("xau", "CMD execute CMD after  a file upload finishes"),
    new Argument("xiu", "CMD execute CMD after  all uploads finish and volume is idle"),
    new Argument("xbc", "CMD execute CMD before a file copy"),
    new Argument("xac", "CMD execute CMD after  a file copy"),
    new Argument("xbr", "CMD execute CMD before a file rename/move"),
    new Argument("xar", "CMD execute CMD after  a file rename/move"),
    new Argument("xbd", "CMD execute CMD before a file delete"),
    new Argument("xad", "CMD execute CMD after  a file delete"),
    new Argument("xm", "CMD execute CMD on message"),
    new Argument("xban", "CMD execute CMD if someone gets banned"),
    new Argument("grid", "show grid/thumbnails by default"),
    new Argument("gsel", "select files in grid by ctrl-click"),
    new Argument("sort", "default sort order"),
    new Argument("nsort", "natural-sort of leading digits in filenames"),
    new Argument("hsortn", "number of sort-rules to add to media URLs"),
    new Argument("ufavico", "URL per-volume favicon (.ico/png/gif/svg)"),
    new Argument("bg-img", "background image url"),
    new Argument("unlist", "dont list files matching REGEX"),
    new Argument("dothidden", "enable support for .hidden files"),
    new Argument("dlni", "force-download (no-inline) files on click"),
    new Argument("html_head", "TXT includes TXT in the <head>, or @PATH for file at PATH"),
    new Argument("html_head_s", "TXT additional static text in the html <head>"),
    new Argument("tcolor", "#fc0 theme color (a hint for webbrowsers, discord, etc.)"),
    new Argument("nodirsz", "don't show total folder size"),
    new Argument("du_who", "all show disk-usage info to everyone"),
    new Argument("robots", "allows indexing by search engines (default)"),
    new Argument("norobots", "kindly asks search engines to leave"),
    new Argument("unlistcr", "don't list read-access in controlpanel"),
    new Argument("unlistcw", "don't list write-access in controlpanel"),
    new Argument("prologues", ".prologue.html files to embed above/before files"),
    new Argument("epilogues", ".epilogue.html files to embed below/after files"),
    new Argument("readmes", "readme.md,README.md files to embed as readmes"),
    new Argument("preadmes", "preadme.md,PREADME.md files to embed as preadmes"),
    new Argument("no_sb_md", "disable js sandbox for markdown files"),
    new Argument("no_sb_lg", "disable js sandbox for prologue/epilogue"),
    new Argument("sb_md", "enable js sandbox for markdown files (default)"),
    new Argument("sb_lg", "enable js sandbox for prologue/epilogue (default)"),
    new Argument("md_sbf", "list of markdown-sandbox safeguards to disable"),
    new Argument("lg_sbf", "list of *logue-sandbox safeguards to disable"),
    new Argument("md_sba", "value of iframe allow-prop for markdown-sandbox"),
    new Argument("lg_sba", "value of iframe allow-prop for *logue-sandbox"),
    new Argument("nohtml", "return html and markdown as text/html"),
    new Argument("noscript", "disable most javascript by use of CSP"),
    new Argument("ui_noacci", "hide account-info in the UI"),
    new Argument("ui_nocpla", "hide cpanel-link in the UI"),
    new Argument("ui_nolbar", "hide link-bar in the UI"),
    new Argument("ui_nombar", "hide top-menu in the UI"),
    new Argument("ui_nonav", "hide navpane+breadcrumbs in the UI"),
    new Argument("ui_notree", "hide navpane in the UI"),
    new Argument("ui_norepl", "hide repl-button in the UI"),
    new Argument("ui_nosrvi", "hide server-info in the UI"),
    new Argument("ui_noctxb", "hide context-buttons in the UI"),
    new Argument("og", "enable OG (disables hotlinking)"),
    new Argument("og_site", "sitename; defaults to --name, disable with '-'"),
    new Argument("og_desc", "description text for all files; disable with '-'"),
    new Argument("og_th", "jf thumbnail format; j / jf / jf3 / w / w3 / ..."),
    new Argument("og_title_a", "audio title format; default: {{ artist }} - {{ title }}"),
    new Argument("og_title_v", "video title format; default: {{ title }}"),
    new Argument("og_title_i", "image title format; default: {{ title }}"),
    new Argument("og_title", "foo fallback title if there's nothing in the db"),
    new Argument("og_s_title", "force default title; do not read from tags"),
    new Argument("og_tpl", "custom html; see --og-tpl in --help"),
    new Argument("og_no_head", "you want to add tags manually with og_tpl"),
    new Argument("og_ua", "if defined: only send OG html if useragent matches this regex"),
    new Argument("opds", "enable OPDS"),
    new Argument("opds_exts", "file formats to list in OPDS feeds; leave empty to show everything"),
    new Argument("rw_edit", "md,txt only require read+write to edit .md and .txt"),
    new Argument("md_no_br", "newline only on double-newline or two tailing spaces"),
    new Argument("md_hist", "where to put markdown backups; s=subfolder, v=volHist, n=nope"),
    new Argument("exp", "enable textfile expansion; see --help-exp"),
    new Argument("exp_md", "placeholders to expand in markdown files; see --help"),
    new Argument("exp_lg", "placeholders to expand in prologue/epilogue; see --help"),
    new Argument("txt_eol", "lf enable EOL conversion when writing docs (LF or CRLF)"),
    new Argument("notail", "disable ?tail (download a growing file continuously)"),
    new Argument("tail_fd", "1 check if file was replaced (new fd) every 1 sec"),
    new Argument("tail_rate", "0.2 check for new data every 0.2 sec"),
    new Argument("tail_tmax", "30 kill connection after 30 sec"),
    new Argument("tail_who", "2 restrict ?tail access (1=admins,2=authed,3=everyone)"),
    new Argument("rss", "allow '?rss' URL suffix (experimental)"),
    new Argument("rss_sort", "m default sort-order (m/u/n/s)"),
    new Argument("rss_fmt_t", "{fname} default title-format"),
    new Argument("rss_fmt_d", "{album},{.tn} default description-format"),
    new Argument("dots", "allow all users with read-access toenable the option to show dotfiles in listings"),
    new Argument("fk", "8 generates per-file accesskeys,which are then required at the \"g\" permission;keys are invalidated if filesize or inode changes"),
    new Argument("fka", "8 generates slightly weaker per-file accesskeys,which are then required at the \"g\" permission;not affected by filesize or inode numbers"),
    new Argument("dk", "8 generates per-directory accesskeys,which are then required at the \"g\" permission;keys are invalidated if filesize or inode changes"),
    new Argument("dks", "per-directory accesskeys allow browsing into subdirs"),
    new Argument("dky", "allow seeing files (not folders) inside a specific folderwith \"g\" perm, and does not require a valid dirkey to do so"),
    new Argument("rmagic", "expensive analysis for mimetype accuracy"),
    new Argument("shr_who", "auth who can create shares? no/auth/a"),
    new Argument("unp_who", "2 unpost only if same... 1=ip+name, 2=ip, 3=name"),
    new Argument("ups_who", "2 restrict viewing the list of recent uploads"),
    new Argument("zip_who", "2 restrict access to download-as-zip/tar"),
    new Argument("zipmaxn", "9k reject download-as-zip if more than 9000 files"),
    new Argument("zipmaxs", "2g reject download-as-zip if size over 2 GiB"),
    new Argument("zipmaxt", "no reply with 'no' if download-as-zip exceeds max"),
    new Argument("zipmaxu", "zip-size-limit does not apply to authenticated users"),
    new Argument("nopipe", "disable race-the-beam (download unfinished uploads)"),
    new Argument("cachectl", "no-cache controls caching in webbrowsers"),
    new Argument("mv_retry", "ms-windows: timeout for renaming busy files"),
    new Argument("rm_retry", "ms-windows: timeout for deleting busy files"),
    new Argument("nospawn", "don't create volume's folder if not exist"),
    new Argument("assert_root", "crash on startup if volume's folder not exist"),
    new Argument("davauth", "ask webdav clients to login for all folders"),
    new Argument("davrt", "show lastmod time of symlink destination, not the link itself(note: this option is always enabled for recursive listings)"),
]


// main code ________________________________________________________________________________________________


ebi('rpre').value = sread('rprefix') ?? 'python -m copyparty'
ebi('rpre').oninput = function(){
    swrite('rprefix', this.value)
}

// get flags
var flagsConf = jread("flagsConf", []);

// these flags have a better, feature-complete way to be configured
var uiOnlyFlags = QSA('input[data-flag]')
function loadUiFlags(){
    for(var i = 0; i < uiOnlyFlags.length; i++){
        var elem = uiOnlyFlags[i]
        var cmd = elem.getAttribute('data-flag')
        var val = flagsConf.filter((f) => f.cmd == cmd)[0]?.value;
        if(elem && val){
            var n = cmd + '+'
            var o = QS('input[data-flag="' + n + '"]');
            if(o){
                var arr = val.split(',')
                elem.value = arr[0];
                var j = 1
                while(o){
                    var val2 = arr[j]
                    if(val2){
                        var prefix = o.getAttribute('data-prefix');
                        if(prefix) val2 = val2.replace(prefix, '')
                        o.value = val2
                    }
                    n += '+'
                    j++;
                    o = QS('input[data-flag="' + n + '"]');
                }
            }
            else{
                elem.value = val
            }
        }
        elem.oninput = uiOptInput;
    }
};
var uiOptInput = function(){
    var cmd = this.getAttribute('data-flag');
    if(!cmd) return;
    var e1 = this;
    if(cmd.endsWith('+')){
        cmd = cmd.replaceAll('+', '');
        e1 = QS('input[data-flag="' + cmd + '"]')
    }
    var val = e1.value
    
    // collect all parts of cmd
    var n = cmd + '+'
    var o = QS('input[data-flag="' + n + '"]');
    if(o){
        while(o){
            if(o.value){
                var prefix = o.getAttribute('data-prefix');
                val += ',' + (prefix ? prefix : '') + o.value;
            }
            n += '+'
            o = QS('input[data-flag="' + n + '"]');
        }
    }

    if(val){
        var f = flagsConf.filter((f) => f.cmd == cmd)[0]
        if(!f)
            flagsConf.push({cmd: cmd, value: val});
        else
            f.value = val;
    }
    else{
        var f = flagsConf.filter((f) => f.cmd == cmd)[0]
        if(!f) return;
        var index = flagsConf.indexOf(f)
        console.log("removing arg at index " + index)
        flagsConf.splice(index, 1)
    }
    jwrite("flagsConf", flagsConf);
}
loadUiFlags();

function loadFlags(){
    var container = ebi('flags');
    container.innerHTML = ""
    for (var i = 0; i < flagsConf.length; i++) {
        if(QS('input[data-flag="' + flagsConf[i].cmd + '"]')) continue;
        var a = mknod("div");
        var flag = flags.filter((f) => f.cmd == flagsConf[i].cmd)[0];
        a.setAttribute("Title", flag?.help);
        a.setAttribute("ref", i);
        a.innerHTML = '<a href="' + 'https://copyparty.eu/cli/#g' + flagsConf[i].cmd.replace("--", "-") + '">' + flagsConf[i].cmd + "</a>\n";
        var inp = mknod("input");
        inp.setAttribute("value", flagsConf[i].value);
        if(flag?.help.match(/\(default:/)){
            var ph = flag.help.match(/(?:\(default:)(.*)(?:\))/)[1]
            ph = ph.trim()
            inp.setAttribute("placeholder", ph);
            // if(!ph.match(/[^0-9]/))
            //     inp.setAttribute("type", "number");
            if(ph.toLowerCase() == "false"){
                inp.setAttribute("disabled", "")
                clmod(a, "binary", true)
            }
        }
        inp.oninput = function(e){
            flagsConf[this.parentNode.getAttribute("ref")].value = this.value;
            jwrite("flagsConf", flagsConf);
        }
        a.appendChild(inp);
        var b = mknod("button", "", "×");
        clmod(b, "delBtn", true);
        b.value = i
        b.onclick = function(){
            console.log("removing arg at index " + this.value)
            flagsConf.splice(this.value, 1)
            loadFlags();
            jwrite("flagsConf", flagsConf);
        }
        a.appendChild(b)
        container.appendChild(a)
    }
}
console.log(flagsConf);
loadFlags();

// based on https://www.w3schools.com/howto/howto_js_autocomplete.asp
var currentFocus;
function addActive(x) {
    if (!x) return false;
    removeActive(x);
    if (currentFocus >= x.length) currentFocus = 0;
    if (currentFocus < 0) currentFocus = (x.length - 1);
    x[currentFocus].classList.add("autocomplete-active");
}
function removeActive(x) {
    for (var i = 0; i < x.length; i++) {
        x[i].classList.remove("autocomplete-active");
    }
}
function closeAllLists(elmnt) {
    var x = document.getElementsByClassName("autocomplete-list");
    for (var i = 0; i < x.length; i++) {
        if (elmnt != x[i]) {
        x[i].parentNode.removeChild(x[i]);
        }
    }
}
document.addEventListener("click", function (e) {
    if(clgot(e.target, 'autocomplete'))
        closeAllLists(ebi(e.target.id + '-list'))
    else
        closeAllLists(e.target);
});
function autocompleteFlags(inp, arr) {
    inp.onclick = 
    inp.oninput = function(e) {
        var a, b, i, val = this.value.trim().split(" ")[this.value.split(" ").length - 1];
        closeAllLists();
        currentFocus = -1;
        if(!val) return;
        a = mknod("DIV", this.id + "-list");
        clmod(a, "autocomplete-list", true)
        this.parentNode.appendChild(a);
        
        function iClick(e){
            var val = this.getElementsByTagName("input")[0].value;
            inp.value = "";
            closeAllLists();
            flagsConf.push({cmd: val, value: ""});

            console.log(flagsConf);
            loadFlags();
            jwrite("flagsConf", flagsConf);

            inp.focus();
        }

        var leftovers = [];
        for (i = 0; i < arr.length; i++) {
            // check if cmd contains query
            if (arr[i].cmd.toUpperCase().match(val.toUpperCase())) {
                b = mknod("DIV");
                b.innerHTML = "<strong>" + arr[i].cmd + "</strong>\n";
                b.innerHTML += arr[i].help;
                b.innerHTML += "<input type='hidden' value='" + arr[i].cmd + "'>";
                b.onclick = iClick;
                a.appendChild(b);
            }
            else{
                leftovers.push(arr[i])
            }
        }
        // achieves basic sorting prio by appending help text matches to the dropdown later
        for (i = 0; i < leftovers.length; i++) {
            // check if help text contains query
            if (leftovers[i].help.toUpperCase().match(val.toUpperCase())) {
                b = mknod("DIV");
                b.innerHTML = "<strong>" + leftovers[i].cmd + "</strong>\n";
                b.innerHTML += leftovers[i].help;
                b.innerHTML += "<input type='hidden' value='" + leftovers[i].cmd + "'>";
                b.onclick = iClick;
                a.appendChild(b);
            }
        }
        
    };
    inp.addEventListener("keydown", function(e) {
        var x = ebi(this.id + "-list");
        if (x) x = x.getElementsByTagName("div");
        if (e.keyCode == 40) {
            ev(e);
            currentFocus++;
            addActive(x);
        } else if (e.keyCode == 38) { //up
            ev(e);
            currentFocus--;
            addActive(x);
        } else if (e.keyCode == 13) {
            e.preventDefault();
            if (currentFocus > -1) {
                if (x) x[currentFocus].click();
            }
        }
    });
}
function autocompleteVolFlags(inp, arr, index) {
    inp.onclick = 
    inp.oninput = function(e) {
        var a, b, i, val = this.value.trim().split(" ")[this.value.split(" ").length - 1];
        closeAllLists();
        currentFocus = -1;
        if(!val) return;
        a = mknod("DIV", this.id + "-list");
        clmod(a, "autocomplete-list", true)
        this.parentNode.appendChild(a);
        
        function iClick(e){
            var val = this.getElementsByTagName("input")[0].value;
            inp.value = "";
            closeAllLists();
            volsConf[index].flags.push({cmd: val, value: ""});

            console.log(volsConf[index].flags);
            loadVolumes();
            jwrite("volsConf", volsConf);

            inp.focus();
        }

        var leftovers = [];
        for (i = 0; i < arr.length; i++) {
            // check if cmd contains query
            if (arr[i].cmd.toUpperCase().match(val.toUpperCase())) {
                b = mknod("DIV");
                b.innerHTML = "<strong>" + arr[i].cmd + "</strong>\n";
                b.innerHTML += arr[i].help;
                b.innerHTML += "<input type='hidden' value='" + arr[i].cmd + "'>";
                b.onclick = iClick;
                a.appendChild(b);
            }
            else{
                leftovers.push(arr[i])
            }
        }
        // achieves basic sorting prio by appending help text matches to the dropdown later
        for (i = 0; i < leftovers.length; i++) {
            // check if help text contains query
            if (leftovers[i].help.toUpperCase().match(val.toUpperCase())) {
                b = mknod("DIV");
                b.innerHTML = "<strong>" + leftovers[i].cmd + "</strong>\n";
                b.innerHTML += leftovers[i].help;
                b.innerHTML += "<input type='hidden' value='" + leftovers[i].cmd + "'>";
                b.onclick = iClick;
                a.appendChild(b);
            }
        }
        
    };
    inp.addEventListener("keydown", function(e) {
        var x = ebi(this.id + "-list");
        if (x) x = x.getElementsByTagName("div");
        if (e.keyCode == 40) {
            ev(e);
            currentFocus++;
            addActive(x);
        } else if (e.keyCode == 38) { //up
            ev(e);
            currentFocus--;
            addActive(x);
        } else if (e.keyCode == 13) {
            e.preventDefault();
            if (currentFocus > -1) {
                if (x) x[currentFocus].click();
            }
        }
    });
}
autocompleteFlags(ebi('flagSearch'), flags);

// alternative call that hides flags that have a better UI method
//autocompleteFlags(ebi('flagSearch'), flags.filter((arg) => !QS('input[data-flag="' + arg.cmd + '"]')));


// users
var usrsConf = jread("usrsConf", []);
function loadUsers(){
    var container = ebi('users');
    container.innerHTML = ""
    for (var i = 0; i < usrsConf.length; i++) {
        var a = mknod("form");
        a.setAttribute("ref", i);
        
        var handle = mknod('p', '', '::::')
        clmod(handle, 'dhandle', true)
        handle.setAttribute('draggable', true)
        handle.ondragstart = function(e){
		    e.dataTransfer.setData("text", ', ' + usrsConf[this.parentNode.getAttribute("ref")].name);
        }
        a.appendChild(handle)

        var inp = mknod("input");
        inp.setAttribute("value", usrsConf[i].name)
        inp.setAttribute("placeholder", "username")
        inp.setAttribute("autocomplete", "new-password")
        clmod(inp, "name", true)
        inp.oninput = function(e){
            usrsConf[this.parentNode.getAttribute("ref")].name = this.value;
            jwrite("usrsConf", usrsConf);
        }
        a.appendChild(inp);

        var inp2 = mknod("input");
        inp2.setAttribute("value", usrsConf[i].pw)
        inp2.setAttribute("type", "password")
        inp2.setAttribute("placeholder", "password")
        inp2.setAttribute("autocomplete", "new-password")
        clmod(inp2, "pw", true)
        inp2.oninput = function(e){
            usrsConf[this.parentNode.getAttribute("ref")].pw = this.value;
            jwrite("usrsConf", usrsConf);
        }
        a.appendChild(inp2);

        var b = mknod("button", "", "×");
        clmod(b, "delBtn", true);
        b.value = i
        b.onclick = function(){
            console.log("removing user at index " + this.value)
            usrsConf.splice(this.value, 1)
            loadUsers();
            jwrite("usrsConf", usrsConf);
        }
        a.appendChild(b)
        container.appendChild(a)
    }
}
loadUsers();

ebi('addUser').onclick = function(){
    usrsConf.push({name: "", pw: "", grp: ""});

    console.log(usrsConf);
    loadUsers();
    
    var ins = QSA('#users .name')
    ins[ins.length - 1].focus();
}

var groups = jread("groupsConf", []);
function loadGroups(){
    var container = ebi('groups');
    container.innerHTML = ""
    for (var i = 0; i < groups.length; i++) {
        var a = mknod("div");
        a.setAttribute("ref", i);

        var inp = mknod("input");
        inp.setAttribute("value", groups[i].name)
        inp.setAttribute("placeholder", "group name")
        clmod(inp, "name", true)
        inp.oninput = function(e){
            groups[this.parentNode.getAttribute("ref")].name = this.value;
            jwrite("groupsConf", groups);
        }
        a.appendChild(inp);

        var inp2 = mknod("input");
        inp2.setAttribute("value", groups[i].users)
        inp2.setAttribute("placeholder", "(drag users here, or type)")
        clmod(inp2, "users", true)
        inp2.oninput = function(e){
            while(this.value.startsWith(',') || this.value.startsWith(' ')) this.value = this.value.slice(1);
            groups[this.parentNode.getAttribute("ref")].users = this.value;
            jwrite("groupsConf", groups);
        }
        a.appendChild(inp2);

        var b = mknod("button", "", "×");
        clmod(b, "delBtn", true);
        b.value = i
        b.onclick = function(){
            console.log("removing group at index " + this.value)
            groups.splice(this.value, 1)
            loadGroups();
            jwrite("groupsConf", groups);
        }
        a.appendChild(b)
        container.appendChild(a)
    }
}
loadGroups();
ebi('addGrp').onclick = function(){
    groups.push({name: "", users: ""});

    loadGroups();
    
    var ins = QSA('#groups .name')
    ins[ins.length - 1].focus();
}

// volumes
var volsConf = jread("volsConf", []);
function loadVolumes(){
    var container = ebi('volumes');
    container.innerHTML = ""

    var srcInput = function(){
        volsConf[this.parentNode.parentNode.getAttribute("ref")].src = this.value;
        jwrite("volsConf", volsConf);
    }
    var dstInput = function(){
        volsConf[this.parentNode.parentNode.getAttribute("ref")].dst = this.value;
        jwrite("volsConf", volsConf);
    }
    for (var i = 0; i < volsConf.length; i++) {
        var a = mknod("div");
        a.setAttribute("ref", i);

        var h = mknod("p", "", "Volume #" + i)
        a.appendChild(h);

        var h3_1 = mknod("h3", "", "real path");
        var inp = mknod("input", "rp" + i, volsConf[i].src);
        inp.setAttribute("value", volsConf[i].src);
        inp.setAttribute("placeholder", "/storage/emulated/0/files");
        clmod(inp, "src", true);
        inp.oninput = srcInput;
        h3_1.appendChild(inp);
        a.appendChild(h3_1);

        a.appendChild(document.createTextNode("➡️"));

        var h3_2 = mknod("h3", "", "virtual path");
        var inp2 = mknod("input", "vp" + i, volsConf[i].dst);
        inp2.setAttribute("value", volsConf[i].dst);
        inp2.setAttribute("placeholder", "/");
        clmod(inp2, "dst", true);
        inp2.oninput = dstInput;
        h3_2.appendChild(inp2);
        a.appendChild(h3_2);

        var pbtn = mknod("button", "", "⚙️ permissions")
        pbtn.setAttribute("value", i)
        pbtn.onclick = showPermConf;
        a.appendChild(pbtn)

        var h3_3 = mknod("h3", "", "volume settings")
        clmod(h3_3, "h_vcfg", true)
        a.appendChild(h3_3)

        if(volsConf[i].flags == undefined)
            volsConf[i].flags = []

        var vfc = mknod("div", "vfc" + i)
        for(var j = 0; j < volsConf[i].flags.length; j++){
            var a2 = mknod("div");
            var flag = volflags.filter((f) => f.cmd == volsConf[i].flags[j].cmd)[0];
            a2.setAttribute("Title", flag?.help);
            a2.setAttribute("vol", i);
            a2.setAttribute("ref", j);
            a2.innerHTML = (
                "<strong>" + volsConf[i].flags[j].cmd + "</strong>"
            );
            var inp3 = mknod("input");
            inp3.setAttribute("value", volsConf[i].flags[j].value);
            if(flag?.help.match(/\(default:/)){
                var ph = flag.help.match(/(?:\(default:)(.*)(?:\))/)[1]
                ph = ph.trim()
                inp3.setAttribute("placeholder", ph);
                if(!ph.match(/[^0-9]/))
                    inp3.setAttribute("type", "number");
            }
            inp3.oninput = function(e){
                volsConf[this.parentNode.getAttribute("vol")]
                    .flags[this.parentNode.getAttribute("ref")]
                    .value = this.value;
                jwrite("volsConf", volsConf);
            }
            a2.appendChild(inp3);
            var b2 = mknod("button", "", "×");
            clmod(b2, "delBtn", true);
            b2.value = i
            b2.onclick = function(){
                console.log("removing volflag at index " + this.value)
                volsConf[this.parentNode.getAttribute("vol")]
                    .flags.splice(this.value, 1)
                loadVolumes();
                jwrite("volsConf", volsConf);
            }
            a2.appendChild(b2)
            vfc.appendChild(a2)
        }
        a.appendChild(vfc)

        var pr = mknod("p", "", "+ add volume setting")
        clmod(pr, "inlinePrompt", true)
        a.appendChild(pr)

        var vf = mknod("input", "vf" + i)
        clmod(vf, "autocomplete", true)
        vf.setAttribute("placeholder", "🔎 volflags");
        autocompleteVolFlags(vf, volflags, i)
        a.appendChild(vf)

        var b = mknod("button", "", "×");
        clmod(b, "delBtn", true);
        b.value = i
        b.onclick = function(){
            console.log("removing volume at index " + this.value)
            volsConf.splice(this.value, 1)
            loadVolumes();
            jwrite("volsConf", volsConf);
        }
        a.appendChild(b)
        container.appendChild(a)
    }
}
loadVolumes();

var perms = [
    {letter: "r", desc: "read: list folder contents, download files"},
    {letter: "w", desc: 'write: upload files; need "r" to see the uploads'},
    {letter: "m", desc: 'move: move files and folders; need "w" at destination'},
    {letter: "d", desc: "delete: permanently delete files and folders"},
    {letter: "g", desc: "get: download files, but cannot see folder contents"},
    {letter: "G", desc: 'upget: "get", but can see filekeys of their own uploads'},
    {letter: "h", desc: 'html: "get", but folders return their index.html'},
    {letter: ".", desc: "dots: user can ask to show dotfiles in listings"},
    {letter: "a", desc: "admin: can see uploader IPs, config-reload"},
    {letter: "A", desc: 'all: same as "rwmda." (read/write/move/delete/admin/dotfiles)'},
]
function loadPerms(vol){
    var container = ebi('perm-list')
    container.innerHTML = ""
    var volume = volsConf[vol]
    ebi('h_perms').innerHTML = "permissions for " + (volume.dst.length > 0 ? volume.dst : "home")
    var users = []
    for(var i = 0; i < groups.length; i++){
        users.push({name: '@' + groups[i].name})
    }
    users = users.concat(usrsConf)
    for(var i = -1; i < users.length; i++){
        var usr = i > -1 ? users[i] : {name: "everyone"};
        var aperms = volume.perms ?? []
        var uperms = aperms.filter((o) => o.user == usr.name)[0]
        var a = mknod("div")
        a.setAttribute("ref", i);
        
        var h = mknod("p", "", usr.name)
        a.appendChild(h)

        var b = mknod("div")
        for(var j = 0; j < perms.length; j++){
            var cid = "upc" + i.toString() + j.toString()
            var c = mknod("input", cid)
            c.setAttribute("type", "checkbox")
            c.setAttribute("uid", i);
            c.setAttribute("p", perms[j].letter);
            if(uperms?.perms.includes(perms[j].letter))
                c.setAttribute("checked", "")
            c.setAttribute("Title", perms[j].desc)
            c.onclick = function(){
                var p = this.getAttribute("p")
                var uid = this.getAttribute("uid")
                var usr = uid > -1 ? users[uid] : {name: "everyone"}
                var o = aperms.filter((o) => o.user == usr.name)[0]
                if(!o){
                    o = {user: usr.name, perms: ""}
                    aperms.push(o)
                }
                if(!o.perms.includes(p))
                    o.perms += p
                else
                    o.perms = o.perms.replace(p, "")
                volume.perms = aperms
            }
            b.appendChild(c)

            var l = mknod("label", "", perms[j].letter)
            l.setAttribute("for", cid)
            l.setAttribute("Title", perms[j].desc)
            b.appendChild(l)
        }
        a.appendChild(b)
        container.appendChild(a)
    }
}
function showPermConf(){
    var index = this.value
    if(index != undefined && index !== ""){
        loadPerms(index)
    }
    else{
        jwrite("volsConf", volsConf);
        console.log(volsConf)
    }
    clmod(ebi('perms-modal'), 'vis', 't');
}
ebi('m_close').onclick =
ebi('m_closeArea').onclick =
    showPermConf;

ebi('addVol').onclick = function(){
    volsConf.push({src: "", dst: "", perms: []});

    console.log(volsConf);
    loadVolumes();
    
    var ins = QSA('#volumes .src')
    ins[ins.length - 1].focus();
}


// config generation
function getConfig(){
    var conf = ebi('rpre').value + ' ';

    for(var i = 0; i < flagsConf.length; i++){
        var val = flagsConf[i].value;
        if(val.match(' ') && !val.startsWith('"'))
            val = '"' + val + '"';
        // checkboxes set text value to 'on'
        conf += [flagsConf[i].cmd, (val != 'on' ? val : '')].join(" ") + " ";
    }

    for(var i = 0; i < usrsConf.length; i++){
        if(usrsConf[i].pw != "")
            conf += "-a " + [usrsConf[i].name, usrsConf[i].pw].join(":") + " "
    }

    for(var i = 0; i < groups.length; i++){
        if(groups[i].name != "" && groups[i].users != "")
            conf += "--grp " + [groups[i].name, groups[i].users.replaceAll(' ', ',').replaceAll(',,', ',')].join(":") + " "
    }

    for(var i = 0; i < volsConf.length; i++){
        conf += "-v " + volsConf[i].src + ":" + volsConf[i].dst
        var a = volsConf[i].perms.filter((u) => u.user === 'everyone')
        var b = volsConf[i].perms.filter((u) => u.user !== 'everyone')
        volsConf[i].perms = [...a, ...b]
        for(var j = 0; j < volsConf[i].perms.length; j++){
            var uname = volsConf[i].perms[j].user
            if(uname)
                conf += ":" + volsConf[i].perms[j].perms + 
                    (uname != "everyone" ? "," + uname : "")
        }
        for(var j = 0; j < volsConf[i].flags.length; j++){
            conf += ":c," + volsConf[i].flags[j].cmd.replaceAll('-', '_') + (volsConf[i].flags[j].value ? '="' + volsConf[i].flags[j].value + '"' : '')
        }
        conf += ": "
    }

    return conf;
}
ebi('copyBtn').onclick = function(){
    cliptxt(getConfig(), function(){
        var a = ebi('copyBtn').innerHTML;
        ebi('copyBtn').innerHTML = "✅";
        setTimeout(function(){ebi('copyBtn').innerHTML = a;}, 1000);
    });
}


J_CFG = 2;
