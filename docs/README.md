**NOTE:** there's more stuff (sharex config, service scripts, nginx configs, ...) in [`/contrib/`](/contrib/)



# example resource files

can be provided to copyparty to tweak things



## example `.epilogue.html`
save one of these as `.epilogue.html` inside a folder to customize it:

* [`minimal-up2k.html`](minimal-up2k.html) will [simplify the upload ui](https://user-images.githubusercontent.com/241032/118311195-dd6ca380-b4ef-11eb-86f3-75a3ff2e1332.png)



## example browser-css
point `--css-browser` to one of these by URL:

* [`browser.css`](browser.css) changes the background
* [`browser-icons.css`](browser-icons.css) adds filetype icons



# other stuff

## [`rclone.md`](rclone.md)
* notes on using rclone as a fuse client/server

## [`example.conf`](example.conf)
* example config file for `-c` (supports accounts, volumes, and volume-flags)
