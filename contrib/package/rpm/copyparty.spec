Name:           copyparty
Version:        $pkgver
Release:        $pkgrel
License:        MIT
Group:          Utilities
URL:            https://github.com/9001/copyparty
Source0:        copyparty-$pkgver.tar.gz
Summary:        File server with accelerated resumable uploads, dedup, WebDAV, FTP, TFTP, zeroconf, media indexer, thumbnails++
BuildArch:      noarch
BuildRequires:  python3, python3-devel, pyproject-rpm-macros, python-setuptools, python-wheel, make
Requires:       python3, (python3-jinja2 or python-jinja2), lsof
Recommends:     ffmpeg, (golang-github-cloudflare-cfssl or cfssl), python-mutagen, python-pillow, python-pyvips
Recommends:     qm-vamp-plugins, python-argon2-cffi, (python-pyopenssl or pyopenssl), python-impacket

%description
Portable file server with accelerated resumable uploads, dedup, WebDAV, FTP, TFTP, zeroconf, media indexer, thumbnails++ all in one file, no deps

See release at https://github.com/9001/copyparty/releases

%global debug_package %{nil}

%generate_buildrequires
%pyproject_buildrequires

%prep
%setup -q

%build
cd "copyparty/web"
make
cd -
%pyproject_wheel

%install
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_libdir}/systemd/{system,user}
mkdir -p %{buildroot}/etc/%{name}
mkdir -p %{buildroot}/var/lib/%{name}-jail
mkdir -p %{buildroot}%{_datadir}/licenses/%{name}

%pyproject_install
%pyproject_save_files copyparty

install -m 0755 bin/prisonparty.sh                       %{buildroot}%{_bindir}/prisonpary.sh
install -m 0644 contrib/systemd/%{name}.conf             %{buildroot}/etc/%{name}/%{name}.conf
install -m 0644 contrib/systemd/%{name}@.service         %{buildroot}%{_libdir}/systemd/system/%{name}@.service
install -m 0644 contrib/systemd/%{name}-user.service     %{buildroot}%{_libdir}/systemd/user/%{name}.service
install -m 0644 contrib/systemd/prisonparty@.service     %{buildroot}%{_libdir}/systemd/system/prisonparty@.service
install -m 0644 contrib/systemd/index.md                 %{buildroot}/var/lib/%{name}-jail/README.md
install -m 0644 LICENSE                                  %{buildroot}%{_datadir}/licenses/%{name}/LICENSE

%files -n copyparty -f %{pyproject_files}
%license LICENSE
%{_bindir}/copyparty
%{_bindir}/partyfuse
%{_bindir}/u2c
%{_bindir}/prisonpary.sh
/etc/%{name}/%{name}.conf
%{_libdir}/systemd/system/%{name}@.service
%{_libdir}/systemd/user/%{name}.service
%{_libdir}/systemd/system/prisonparty@.service
/var/lib/%{name}-jail/README.md
