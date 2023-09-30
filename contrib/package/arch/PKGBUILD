# Maintainer: icxes <dev.null@need.moe>
pkgname=copyparty
pkgver="1.9.7"
pkgrel=1
pkgdesc="Portable file sharing hub"
arch=("any")
url="https://github.com/9001/${pkgname}"
license=('MIT')
depends=("python" "lsof" "python-jinja")
makedepends=("python-wheel" "python-setuptools" "python-build" "python-installer" "make" "pigz")
optdepends=("ffmpeg: thumbnails for videos, images (slower) and audio, music tags"
            "python-mutagen: music tags (alternative)" 
            "python-pillow: thumbnails for images" 
            "python-pyvips: thumbnails for images (higher quality, faster, uses more ram)" 
            "libkeyfinder-git: detection of musical keys" 
            "qm-vamp-plugins: BPM detection" 
            "python-pyopenssl: ftps functionality" 
            "python-argon2_cffi: hashed passwords in config" 
            "python-impacket-git: smb support (bad idea)"
)
source=("https://github.com/9001/${pkgname}/releases/download/v${pkgver}/${pkgname}-${pkgver}.tar.gz")
backup=("etc/${pkgname}.d/init" )
sha256sums=("1d427392568ed2048b06b2049cb884f650ff1466e2f57779f0c263d3ae1db311")

build() {
    cd "${srcdir}/${pkgname}-${pkgver}"
    
    pushd copyparty/web
    make -j$(nproc)
    rm Makefile
    popd
    
    python3 -m build -wn
}

package() {
    cd "${srcdir}/${pkgname}-${pkgver}"
    python3 -m installer -d "$pkgdir" dist/*.whl

    install -dm755 "${pkgdir}/etc/${pkgname}.d"
    install -Dm755 "bin/prisonparty.sh" "${pkgdir}/usr/bin/prisonparty"
    install -Dm644 "contrib/package/arch/${pkgname}.conf" "${pkgdir}/etc/${pkgname}.d/init"
    install -Dm644 "contrib/package/arch/${pkgname}.service" "${pkgdir}/usr/lib/systemd/system/${pkgname}.service"
    install -Dm644 "contrib/package/arch/prisonparty.service" "${pkgdir}/usr/lib/systemd/system/prisonparty.service"
    install -Dm644 "contrib/package/arch/index.md" "${pkgdir}/var/lib/${pkgname}-jail/README.md"
    install -Dm644 "LICENSE" "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"

    find /etc/${pkgname}.d -iname '*.conf' 2>/dev/null | grep -qE . && return
    echo "┏━━━━━━━━━━━━━━━──-"
    echo "┃ Configure ${pkgname} by adding .conf files into /etc/${pkgname}.d/"
    echo "┃ and maybe copy+edit one of the following to /etc/systemd/system/:"
    echo "┣━♦ /usr/lib/systemd/system/${pkgname}.service   (standard)"
    echo "┣━♦ /usr/lib/systemd/system/prisonparty.service (chroot)"
    echo "┗━━━━━━━━━━━━━━━──-"
}
