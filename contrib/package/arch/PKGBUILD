# Maintainer: icxes <dev.null@need.moe>
pkgname=copyparty
pkgver="1.7.0"
pkgrel=1
pkgdesc="Portable file sharing hub"
arch=("any")
url="https://github.com/9001/${pkgname}"
license=('MIT')
depends=("python" "lsof")
optdepends=("ffmpeg: thumbnails for videos, images (slower) and audio, music tags" 
            "python-jinja: faster html generator" 
            "python-mutagen: music tags (alternative)" 
            "python-pillow: thumbnails for images" 
            "python-pyvips: thumbnails for images (higher quality, faster, uses more ram)" 
            "libkeyfinder-git: detection of musical keys" 
            "qm-vamp-plugins: BPM detection" 
            "python-pyopenssl: ftps functionality" 
            "python-impacket-git: smb support (bad idea)"
)
source=("${url}/releases/download/v${pkgver}/${pkgname}-sfx.py" 
        "${pkgname}.conf"
        "${pkgname}.service"
        "prisonparty.service"
        "index.md"
        "https://raw.githubusercontent.com/9001/${pkgname}/v${pkgver}/bin/prisonparty.sh"
        "https://raw.githubusercontent.com/9001/${pkgname}/v${pkgver}/LICENSE"
)
backup=("etc/${pkgname}.d/init" )
sha256sums=("096dbe073b796c9ca29425026345b486d57b2752de8c3b6d32fd8c9396c5b602"
            "b8565eba5e64dedba1cf6c7aac7e31c5a731ed7153d6810288a28f00a36c28b2"
            "f65c207e0670f9d78ad2e399bda18d5502ff30d2ac79e0e7fc48e7fbdc39afdc"
            "c4f396b083c9ec02ad50b52412c84d2a82be7f079b2d016e1c9fad22d68285ff"
            "dba701de9fd584405917e923ea1e59dbb249b96ef23bad479cf4e42740b774c8"
            "8e89d281483e22d11d111bed540652af35b66af6f14f49faae7b959f6cdc6475"
            "cb2ce3d6277bf2f5a82ecf336cc44963bc6490bcf496ffbd75fc9e21abaa75f3"
)

package() {
    cd "${srcdir}/"

    install -dm755 "${pkgdir}/etc/${pkgname}.d"
    install -Dm755 "${pkgname}-sfx.py" "${pkgdir}/usr/bin/${pkgname}"
    install -Dm755 "prisonparty.sh" "${pkgdir}/usr/bin/prisonparty"
    install -Dm644 "${pkgname}.conf" "${pkgdir}/etc/${pkgname}.d/init"
    install -Dm644 "${pkgname}.service" "${pkgdir}/usr/lib/systemd/system/${pkgname}.service"
    install -Dm644 "prisonparty.service" "${pkgdir}/usr/lib/systemd/system/prisonparty.service"
    install -Dm644 "index.md" "${pkgdir}/var/lib/${pkgname}-jail/README.md"
    install -Dm644 "LICENSE" "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"

    find /etc/${pkgname}.d -iname '*.conf' 2>/dev/null | grep -qE . && return
    echo "┏━━━━━━━━━━━━━━━──-"
    echo "┃ Configure ${pkgname} by adding .conf files into /etc/${pkgname}.d/"
    echo "┃ and maybe copy+edit one of the following to /etc/systemd/system/:"
    echo "┣━♦ /usr/lib/systemd/system/${pkgname}.service   (standard)"
    echo "┣━♦ /usr/lib/systemd/system/prisonparty.service (chroot)"
    echo "┗━━━━━━━━━━━━━━━──-"
}
