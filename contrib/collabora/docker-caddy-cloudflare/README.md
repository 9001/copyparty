# Collabora example in docker with Caddy reverse proxy and Cloudflare DNS
```
 tree --filesfirst -aFL3 --gitignore -I .keep -I .gitignore -I README.md
.
├── docker-compose.yml          # docker compose file
├── caddy/
│   ├── Caddyfile               # caddy server configuration https://caddyserver.com/docs/caddyfile
│   ├── .env.example            # caddy container environment variables; copy it to caddy/.env and put your cloudflare token there; https://github.com/caddy-dns/cloudflare
│   ├── config/                 # caddy persistence
│   └── data/                   # caddy persistence
├── collabora/
│   └── seccomp-profile.json    # collabora seccomp rules; source: https://raw.githubusercontent.com/CollaboraOnline/online/refs/heads/main/docker/cool-seccomp-profile.json
└── copyparty/
    ├── cfg/                    # copyparty persistence
    │   └── copyparty.conf      # copyparty config file
    └── fileshare/              # copyparty fileshare (mapped to /w inside container)

```

Read the comments in `docker-compose.yml`, `caddy/Caddyfile`, `copyparty/cfg/copyparty.conf`.

To run this example:
```
cp caddy/.env.example caddy/.env && nano caddy/.env
# in nano paste your token for cloudflare DNS management

# set these variables to your copyparty and collabora domain names
PARTY_DOMAIN=
COLLABORA_DOMAIN=

# substitute example domains with supplied domain names
find . -type f -exec sed -i -e 's/party\.example\.org/'"${PARTY_DOMAIN}"'/g' -e 's/office\.example\.org/'"${COLLABORA_DOMAIN}"'/g' {} +

# download collabora seccomp profile
wget -nv -O collabora/seccomp-profile.json -- 'https://raw.githubusercontent.com/CollaboraOnline/online/refs/heads/main/docker/cool-seccomp-profile.json'

# create and run containers
docker compose up -d
```
