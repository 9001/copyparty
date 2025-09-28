> [!WARNING]  
> I am unable to guarantee the quality, safety, and security of anything in this folder; it is a combination of examples I found online. Please submit corrections or improvements 🙏

This example should be enough to get things working. I have confirmed this basic config personally. User creation and management work, however once a user is passed through to copy party, manual editing of the config file will be needed to control new users. i.e. anyone you let through your SSO portal will be granted basic/default settings and permissions, unless manually configured otherwise. 

To control more than just letting users through to your instance, make sure to add the username passed through by authentik to copyparty (default just the authentik username) with a plain password. e.g. :

```
[accounts]
 username: foo
```

This will allow you to use copyparty's existing config mechanisms to manage users from your SSO. Add the relevant user/s to the su group to given them superuser privilleges within copyparty.

Ensure to create the external network proxy (not needed if everything you want behind traefik is is the same docker-compose stack).To create the "proxy" docker network see https://docs.docker.com/reference/cli/docker/network/create/

for an basic example:
 `docker network create -d bridge proxy`

this is based on:
* https://goauthentik.io/docker-compose.yml
* https://goauthentik.io/docs/providers/proxy/server_traefik

incomplete list of modifications made:
* support for running with podman as root on fedora (`:z` volumes, `label:disable`)
v