#!/bin/bash

#--localbuild to build webdeps and tar locally; otherwise just download prebuilt
#--pm change packagemanager; otherwise default to dnf

while [ ! -z "$1" ]; do
	case $1 in
		local-build)  local_build=1  ; ;;
		pm)           shift;packagemanager="$1";  ;;
	esac
	shift
done

[ -e copyparty/__main__.py ] || cd ..
[ -e copyparty/__main__.py ] ||
{
	echo "run me from within the project root folder"
	echo
	exit 1
}


packagemanager=${packagemanager:-dnf}
ver=$(awk '/^VERSION/{gsub(/[^0-9]/," ");printf "%d.%d.%d\n",$1,$2,$3}' copyparty/__version__.py)
releasedir="dist/temp_copyparty_$ver"
sourcepkg="copyparty-$ver.tar.gz"

#make temporary directory to build rpm in
mkdir -p $releasedir/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}
trap "rm -rf $releasedir/" EXIT

# make/get tarball
if [ $local_build ]; then 
    if [ ! -f "copyparty/web/deps/mini-fa.woff" ]; then
        sudo $packagemanager update
        sudo $packagemanager install podman-docker docker
        make -C deps-docker
    fi
    if [ ! -f "dist/$sourcepkg" ]; then
        ./$cppdir/scripts/make-tgz-release.sh "$ver"
    fi
else
    if [ ! -f "dist/$sourcepkg" ]; then
        curl -OL https://github.com/9001/copyparty/releases/download/v$ver/$sourcepkg --output-dir dist
    fi
fi

cp dist/$sourcepkg "$releasedir/SOURCES/$sourcepkg"

cp "contrib/package/rpm/copyparty.spec" "$releasedir/SPECS/"
sed -i "s/\$pkgver/$ver/g" "$releasedir/SPECS/copyparty.spec"
sed -i "s/\$pkgrel/1/g"  "$releasedir/SPECS/copyparty.spec"

sudo $packagemanager update
sudo $packagemanager install rpmdevtools python-wheel python-setuptools pyproject-rpm-macros
cd "$releasedir/"
rpmbuild --define "_topdir `pwd`" -bb SPECS/copyparty.spec
cd -

rpm="copyparty-$ver-1.noarch.rpm"
mv "$releasedir/RPMS/noarch/$rpm" dist/$rpm
