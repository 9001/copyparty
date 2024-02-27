> [!WARNING]  
> I am unable to guarantee the quality, safety, and security of anything in this folder; it is a combination of examples I found online. Please submit corrections or improvements 🙏

to try this out with minimal adjustments:
* specify what filesystem-path to share with copyparty, replacing the default/example value `/srv/pub` in `docker-compose.yml`
* add `127.0.0.1 fs.example.com traefik.example.com authelia.example.com` to your `/etc/hosts`
* `sudo docker-compose up`
* login to https://fs.example.com/ with username `authelia` password `authelia`

to use this in a safe and secure manner:
* follow a guide on setting up authelia properly (TODO:link) and use the copyparty-specific parts of this folder as inspiration for your own config; namely the `cpp` subfolder and the `copyparty` service in `docker-compose.yml`

this folder is based on:
* https://github.com/authelia/authelia/tree/39763aaed24c4abdecd884b47357a052b235942d/examples/compose/lite

incomplete list of modifications made:
* support for running with podman as root on fedora (`:z` volumes, `label:disable`)
* explicitly using authelia `v4.38.0-beta3` because config syntax changed since last stable release
* disabled automatic letsencrypt certificate signing
* reduced logging from debug to info
* added a warning that traefik is given access to the docker socket (as recommended by traefik docs) which means traefik is able to break out of the container and has full root access on the host machine


# performance

currently **not optimal,** at least when compared to running the python sfx outside of docker... some numbers from my laptop (ryzen4500u/fedora39):

| req/s |  https D/L | http D/L | approach |
| -----:| ----------:|:--------:| -------- |
|  5200 | 1294 MiB/s | 5+ GiB/s | [copyparty-sfx.py](https://github.com/9001/copyparty/releases/latest/download/copyparty-sfx.py) running on host |
|  4370 |  725 MiB/s | 4+ GiB/s | `docker run copyparty/ac` |
|  2420 |  694 MiB/s | n/a      | `copyparty/ac` behind traefik |
|    75 |  694 MiB/s | n/a      | traefik and authelia **(you are here)** |

authelia is behaving strangely, handling 340 requests per second for a while, but then it suddenly drops to 75 and stays there...

I'm assuming all of the performance issues is due to a misconfiguration of authelia/traefik/docker on my end, but I don't relly know where to start
