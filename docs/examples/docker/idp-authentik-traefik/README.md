> [!WARNING]  
> I am unable to guarantee the quality, safety, and security of anything in this folder; it is a combination of examples I found online. Please submit corrections or improvements 🙏

This example should be enough to get things working. I have confirmed this basic config personally. User creation and management work, however once a user is passed through to copy party, manual editing of the config file will be needed to control new users. i.e. anyone you let through your SSO portal will be granted basic/default settings and permissions, unless manually configured otherwise. 

this is based on:
* https://goauthentik.io/docker-compose.yml
* https://goauthentik.io/docs/providers/proxy/server_traefik

incomplete list of modifications made:
* support for running with podman as root on fedora (`:z` volumes, `label:disable`)
