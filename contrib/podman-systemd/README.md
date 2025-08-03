# copyparty with Podman and Systemd

Use this configuration is if you want to run copyparty in a Podman container, with the reliability of running the container under a systemd service.

Documentation for `.container` files can be found in the [Container unit](https://docs.podman.io/en/latest/markdown/podman-systemd.unit.5.html#container-units-container) docs. Systemd cannot does not understand `.container` files natively, so Podman converts these to `.service` files with a [systemd-generator](https://www.freedesktop.org/software/systemd/man/latest/systemd.generator.html). This process is transparent, but sometimes needs to be debugged in case your `.container` file is malformed. There are instructions to debug the systemd generator below.

To run copyparty in this way, you must already have podman installed. To install Podman, see: https://podman.io/docs/installation

There is a sample configuration file in the same directory as this file (`copyparty.conf`).

## Run the container as root

It's simplest, but less secure to run the container as the root user. I'd recommend trying to get it to run this way before trying to run it as non-root.

First, change this line in the `copyparty-root.container` to reflect the directory you want to share. By default, it shares `/mnt/` but you'll probably want to change this.

```
Volume=/mnt:/w:z
```

Note that you can change the owner and group of this share by changing the `uid:` and `gid:` of the volume in `copyparty.conf`, but for simplicity let's assume you want it to be owned by `root:root`.

To install and start copyparty with Podman and systemd as the root user, run the following:

```shell
sudo mkdir -pv /etc/systemd/container/ /etc/copyparty/
sudo cp -v copyparty-root.container /etc/systemd/containers/copyparty.container
sudo cp -v copyparty.conf /etc/copyparty/
sudo systemctl daemon-reload
sudo systemctl enable --now copyparty
```

You can see the status of the service with:

```shell
sudo systemctl status copyparty
```

You can see (and follow) the logs with either of these commands:

```shell
sudo podman logs -f copyparty

# -a is required or else you'll get output like: copyparty[549025]: [649B blob data]
sudo journalctl -a -f -u copyparty
```

If the container fails to start, and you've modified the `.container` service, it's likely that your `.container` file failed to be translated into a `.service` file. You can debug the podman service generator with this command:

```shell
sudo /usr/lib/systemd/system-generators/podman-system-generator --dryrun
```
