# copyparty with Podman and Systemd

Use this configuration if you want to run copyparty in a Podman container, with the reliability of running the container under a systemd service.

Documentation for `.container` files can be found in the [Container unit](https://docs.podman.io/en/latest/markdown/podman-systemd.unit.5.html#container-units-container) docs. Systemd does not understand `.container` files natively, so Podman converts these to `.service` files with a [systemd-generator](https://www.freedesktop.org/software/systemd/man/latest/systemd.generator.html). This process is transparent, but sometimes needs to be debugged in case your `.container` file is malformed. There are instructions to debug the systemd generator in the Troubleshooting section below.

To run copyparty in this way, you must already have podman installed. To install Podman, see: https://podman.io/docs/installation

There is a sample configuration file in the same directory as this file (`copyparty.conf`).

## Run the container as root

Running the container as the root user is easy to set up, but less secure. There are instructions in the next section to run the container as a rootless user if you'd rather run the container like that.

First, change this line in the `copyparty.container` file to reflect the directory you want to share. By default, it shares `/mnt/` but you'll probably want to change that.

```
# Change /mnt to something you want to share
Volume=/mnt:/w:z
```

Note that you can select the owner and group of this volume by changing the `uid:` and `gid:` of the volume in `copyparty.conf`, but for simplicity let's assume you want it to be owned by `root:root`.

To install and start copyparty with Podman and systemd as the root user, run the following:

```shell
sudo mkdir -pv /etc/systemd/container/ /etc/copyparty/
sudo cp -v copyparty.container /etc/systemd/containers/
sudo cp -v copyparty.conf /etc/copyparty/
sudo systemctl daemon-reload
sudo systemctl start copyparty
```

Note: You can't "enable" this kind of Podman service. The `[Install]` section of the `.container` file effectively handles enabling the service so that it starts when the server reboots.

You can see the status of the service with:

```shell
sudo systemctl status -a copyparty
```

You can see (and follow) the logs with either of these commands:

```shell
sudo podman logs -f copyparty

# -a is required or else you'll get output like: copyparty[549025]: [649B blob data]
sudo journalctl -a -f -u copyparty
```

## Run the container as a non-root user

This configuration is more secure, but is more involved and requires ensuring files have proper permissions. You will need a root user account to do some of this setup.

First, you need a user to run the container as. In this example we'll create a "podman" user with UID=1001 and GID=1001.

```shell
sudo groupadd -g 1001 podman
sudo useradd -u 1001 -m podman
sudo usermod -aG podman podman
sudo loginctl enable-linger podman
# Set a strong password for this user
sudo -u podman passwd
```

The `enable-linger` command allows the podman user to run systemd user services that persist even when the user is not logged in. You could use a user that already exists in the system to run this service as, just make sure to run `loginctl enable-linger USERNAME` for that user.

Next, change these lines in the `copyparty.container` file to reflect the config directory and the directory you want to share. By default, the config shares `/home/podman/copyparty/sharing/` but you'll probably want to change this:

```
# Change to reflect your non-root user's home directory
Volume=/home/podman/copyparty/config:/cfg:z

# Change to the directory you want to share
Volume=/home/podman/copyparty/sharing:/w:z
```

Make sure the podman user has read/write access to both of these directories.

Next, **log in to the server as the podman user**.

To install and start copyparty as the non-root podman user, run the following:

```shell
mkdir -pv /home/podman/.config/containers/systemd/ /home/podman/copyparty/config
cp -v copyparty.container /home/podman/.config/containers/systemd/copyparty.container
cp -v copyparty.conf /home/podman/copyparty/config
systemctl --user daemon-reload
systemctl --user start copyparty
```

**Important note: Never use `sudo` with `systemctl --user`!**

You can check the status of the user service with:

```shell
systemctl --user status -a copyparty
```

You can see (and follow) the logs with:

```shell
podman logs -f copyparty

journalctl --user -a -f -u copyparty
```

## Troubleshooting

If the container fails to start, and you've modified the `.container` service, it's likely that your `.container` file failed to be translated into a `.service` file. You can debug the podman service generator with this command:

```shell
sudo /usr/lib/systemd/system-generators/podman-system-generator --dryrun
```

## Allowing Traffic from Outside your Server

To allow traffic on port 3923 of your server, you should run:

```shell
sudo firewall-cmd --permanent --add-port=3923/tcp
sudo firewall-cmd --reload
```

Otherwise, you won't be able to access the copyparty server from anywhere other than the server itself.

## Updating copyparty

To update the version of copyparty used in the container, you can:

```shell
# If root:
sudo podman pull docker.io/copyparty/ac:latest
sudo systemctl restart copyparty

# If non-root:
podman pull docker.io/copyparty/ac:latest
systemctl --user restart copyparty
```

Or, you can change the pinned version of the image in the `[Container]` section of the `.container` file and run:

```shell
# If root:
sudo systemctl daemon-reload
sudo systemctl restart copyparty

# If non-root:
systemctl --user daemon-reload
systemctl --user restart copyparty
```

Podman will pull the image you've specified when restarting. If you have it set to `:latest`, Podman does not know to re-pull the container.

### Enabling auto-update

Alternatively, you can enable auto-updates by un-commenting this line:

```
# AutoUpdate=registry
```

You will also need to enable the [podman auto-updater service](https://docs.podman.io/en/latest/markdown/podman-auto-update.1.html) with:

```shell
# If root:
sudo systemctl enable podman-auto-update.timer podman-auto-update.service

# If non-root:
systemctl --user enable podman-auto-update.timer podman-auto-update.service
```

This works best if you always want the latest version of copyparty. The auto-updater runs once every 24 hours.
