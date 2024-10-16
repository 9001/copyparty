# building the images yourself

```bash
./make.sh hclean pull img push
```
will download the latest copyparty-sfx.py from github unless you have [built it from scratch](../../docs/devnotes.md#just-the-sfx) and then build all the images based on that

deprecated alternative: run `make` to use the makefile however that uses docker instead of podman and only builds x86_64

`make.sh` is necessarily(?) overengineered because:
* podman keeps burning dockerhub pulls by not using the cached images (`--pull=never` does not apply to manifests)
* podman cannot build from a local manifest, only local images or remote manifests

but I don't really know what i'm doing here 💩

* auth for pushing images to repos;  
  `podman login docker.io`  
  `podman login ghcr.io -u 9001`  
  [about gchq](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry) (takes a classic token as password)


## building on alpine

```bash
apk add podman{,-docker}
rc-update add cgroups
service cgroups start
vim /etc/containers/storage.conf  # driver = "btrfs"
modprobe tun
echo ed:100000:65536 >/etc/subuid
echo ed:100000:65536 >/etc/subgid
apk add qemu-openrc qemu-tools qemu-{arm,armeb,aarch64,s390x,ppc64le}
rc-update add qemu-binfmt
service qemu-binfmt start
```
