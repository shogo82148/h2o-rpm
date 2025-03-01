%define docroot /var/www

%{?perl_default_filter}
%global __requires_exclude perl\\(VMS|perl\\(Win32|perl\\(Server::Starter

%if 0%{?rhel} >= 8
%define cmake cmake
%else
%define cmake cmake3
%endif

%define requires_brotli 1
%if 0%{?amzn} == 2
%define requires_brotli 0
%endif

Summary: H2O - The optimized HTTP/1, HTTP/2, HTTP/3 server
Name: h2o
Version: 2.3.0
Release: 58%{?dist}
URL: https://h2o.examp1e.net/
Source0: https://github.com/h2o/h2o/archive/26b116e9536be8cf07036185e3edf9d721c9bac2.tar.gz
Source1: index.html
Source2: h2o.logrotate
Source4: h2o.service
Source5: h2o.conf
Source6: https://github.com/tatsuhiro-t/wslay/releases/download/release-1.1.1/wslay-1.1.1.tar.gz
Source7: brotli-1.1.0.tar.gz
Patch1: 01-fix-build.patch
License: MIT
Group: System Environment/Daemons
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
%if %{requires_brotli}
BuildRequires: brotli-devel
Requires: brotli
%endif
BuildRequires: gcc-c++, openssl-devel, pkgconfig, bison, zlib-devel

%if 0%{?amzn} >= 2022
BuildRequires: ruby, ruby-devel, ruby3.1-rubygem-rake
%else
BuildRequires: ruby, ruby-devel, rubygem-rake
%endif
%if 0%{?rhel} >= 8
BuildRequires: cmake
%else
BuildRequires: cmake3
%endif
Requires: openssl, perl, zlib
BuildRequires: systemd-units
Requires(preun): systemd
Requires(postun): systemd
Requires(post): systemd

%description
H2O is a very fast HTTP server written in C

%package -n libh2o
Group: Development/Libraries
Summary: H2O Library compiled with libuv

%description -n libh2o
libh2o package provides H2O library compiled with libuv which allows you to
link your own software to H2O.

%package -n libh2o-evloop
Group: Development/Libraries
Summary: H2O Library compiled with its own event loop

%description -n libh2o-evloop
libh2o-evloop package provides H2O library compiled with its own event loop
which allows you to link your own software to H2O.

%package -n libh2o-devel
Group: Development/Libraries
Summary: Development interfaces for H2O
Requires: openssl-devel, libuv-devel, pkgconfig
Requires: libh2o = %{version}-%{release}
Requires: libh2o-evloop = %{version}-%{release}
Obsoletes: h2o-devel < 3.0

%description -n libh2o-devel
libh2o-devel package provides H2O header files and helpers which allow you to
build your own software using H2O.

%prep
%setup -q -n h2o-26b116e9536be8cf07036185e3edf9d721c9bac2
%patch1 -p1
%build

%if ! %{requires_brotli}
   tar xf %{SOURCE7}
   cd brotli-1.1.0
   mkdir out && cd out
   %cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=%{_prefix} -DCMAKE_INSTALL_LIBDIR=%{_libdir}/h2o ..
   make %{?_smp_mflags} && make install
   cd ../..
   export PKG_CONFIG_PATH=%{_libdir}/h2o/pkgconfig:$PKG_CONFIG_PATH
   export LDFLAGS="-L%{_libdir}/h2o -Wl,-rpath,%{_libdir}/h2o $LDFLAGS"
%endif

LDFLAGS="-no-pie $LDFLAGS"

tar xf %{SOURCE6}
cd wslay-1.1.1
%configure --enable-shared="" --disable-shared --with-pic
make %{?_smp_mflags} && make install
cd ..

mkdir -p build
cd build
%cmake -DWITH_MRUBY=on -DCMAKE_INSTALL_PREFIX=%{_prefix} -DBUILD_SHARED_LIBS=on ..
make %{?_smp_mflags}


%install
rm -rf $RPM_BUILD_ROOT

%if ! %{requires_brotli}
   cd brotli-1.1.0/out
   make DESTDIR=$RPM_BUILD_ROOT install
   cd ../..
%endif

cd build
make DESTDIR=$RPM_BUILD_ROOT install
cd ..

mv $RPM_BUILD_ROOT%{_prefix}/bin \
        $RPM_BUILD_ROOT%{_sbindir}

mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/h2o
install -m 644 -p $RPM_SOURCE_DIR/h2o.conf \
        $RPM_BUILD_ROOT%{_sysconfdir}/h2o/h2o.conf

# docroot
mkdir -p $RPM_BUILD_ROOT%{docroot}/html
install -m 644 -p $RPM_SOURCE_DIR/index.html \
        $RPM_BUILD_ROOT%{docroot}/html/index.html

# Set up /var directories
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/log/h2o

# Install systemd service files
mkdir -p $RPM_BUILD_ROOT%{_unitdir}
install -m 644 -p $RPM_SOURCE_DIR/h2o.service \
	$RPM_BUILD_ROOT%{_unitdir}/h2o.service

mkdir -p $RPM_BUILD_ROOT/run/h2o

# Install tmpfiles.d configuration
mkdir -p $RPM_BUILD_ROOT%{_prefix}/lib/tmpfiles.d
install -m 644 -p $RPM_SOURCE_DIR/h2o.tmpfiles \
	$RPM_BUILD_ROOT%{_prefix}/lib/tmpfiles.d/h2o.conf

# install log rotation stuff
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/logrotate.d
install -m 644 -p $RPM_SOURCE_DIR/h2o.logrotate \
	$RPM_BUILD_ROOT%{_sysconfdir}/logrotate.d/h2o

%define sslcert %{_sysconfdir}/pki/tls/certs/localhost.crt
%define sslkey %{_sysconfdir}/pki/tls/private/localhost.key

%pre

%post
%systemd_post h2o.service

umask 037
if [ -f %{sslkey} -o -f %{sslcert} ]; then
   exit 0
fi

if [ ! -f %{sslkey} ] ; then
%{_bindir}/openssl genrsa -rand /proc/apm:/proc/cpuinfo:/proc/dma:/proc/filesystems:/proc/interrupts:/proc/ioports:/proc/pci:/proc/rtc:/proc/uptime 2048 > %{sslkey} 2> /dev/null
fi

FQDN=`hostname`
if [ "x${FQDN}" = "x" ]; then
   FQDN=localhost.localdomain
fi

if [ ! -f %{sslcert} ] ; then
cat << EOF | %{_bindir}/openssl req -new -key %{sslkey} \
         -x509 -sha256 -days 365 -set_serial $RANDOM -extensions v3_req \
         -out %{sslcert} 2>/dev/null
--
SomeState
SomeCity
SomeOrganization
SomeOrganizationalUnit
${FQDN}
root@${FQDN}
EOF
fi

if [ -f %{sslkey} ]; then
   chgrp nobody %{sslkey}
fi

if [ -f %{sslcert} ]; then
   chgrp nobody %{sslcert}
fi

%preun
%systemd_preun h2o.service

%postun
%systemd_postun h2o.service

%post -n libh2o -p /sbin/ldconfig

%postun -n libh2o -p /sbin/ldconfig

%post -n libh2o-evloop -p /sbin/ldconfig

%postun -n libh2o-evloop -p /sbin/ldconfig

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)

%dir %{_sysconfdir}/h2o
%config(noreplace) %{_sysconfdir}/h2o/h2o.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/h2o

%{_unitdir}/h2o.service

%{_prefix}/lib/tmpfiles.d/h2o.conf

%{_sbindir}/h2o
%{_sbindir}/h2o-httpclient
%{_sbindir}/h2olog
%{_datadir}/h2o/annotate-backtrace-symbols
%{_datadir}/h2o/fastcgi-cgi
%{_datadir}/h2o/fetch-ocsp-response
%{_datadir}/h2o/kill-on-close
%{_datadir}/h2o/setuidgid
%{_datadir}/h2o/start_server

%if ! %{requires_brotli}
   %dir %{_libdir}/h2o
   %{_libdir}/h2o/libbrotlienc.so*
   %{_libdir}/h2o/libbrotlidec.so*
   %{_libdir}/h2o/libbrotlicommon.so*
   %exclude %{_libdir}/h2o/pkgconfig/*.pc
   %exclude /usr/include/brotli/*.h
   %exclude /usr/sbin/brotli
%endif

%{_mandir}/man5/h2o.*
%{_mandir}/man8/h2o.8*

%{_datadir}/h2o/mruby
%{_datadir}/doc

%{_datadir}/h2o/ca-bundle.crt
%{_datadir}/h2o/status

%dir %{docroot}
%dir %{docroot}/html
%config(noreplace) %{docroot}/html/index.html

%attr(0770,root,nobody) %dir /run/h2o
%attr(0700,root,root) %dir %{_localstatedir}/log/h2o

%files -n libh2o
%{_libdir}/libh2o.so.*

%files -n libh2o-evloop
%{_libdir}/libh2o-evloop.so.*

%files -n libh2o-devel
%{_libdir}/libh2o.so
%{_libdir}/libh2o-evloop.so
%{_libdir}/pkgconfig/libh2o.pc
%{_libdir}/pkgconfig/libh2o-evloop.pc
%{_includedir}/h2o.h
%{_includedir}/h2o
%{_includedir}/picotls.h
%{_includedir}/picotls
%{_includedir}/quicly.h
%{_includedir}/quicly

%changelog

* Sat Mar 01 2025 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-58
- bump v2.3.0-26b116e9536be8cf07036185e3edf9d721c9bac2

* Sat Feb 01 2025 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-57
- bump v2.3.0-26b116e9536be8cf07036185e3edf9d721c9bac2

* Wed Jan 01 2025 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-56
- bump v2.3.0-ebcd7f47d89525fd93252a8ba99ca732abda0fdb

* Sun Dec 01 2024 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-55
- bump v2.3.0-d750b56aa929d55d9d18b9d2a7adea53ec898114

* Sun Sep 01 2024 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-54
- bump v2.3.0-c54c63285b52421da2782f028022647fc2ea3dd1

* Thu Aug 01 2024 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-53
- bump v2.3.0-840ee16ead9683e95170cdc8742db2bc02748ed3

* Mon Jul 01 2024 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-52
- bump v2.3.0-16b13eee8ad7895b4fe3fcbcabee53bd52782562

* Sat Jun 01 2024 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-51
- bump v2.3.0-aee409f9ae648bbd3899d92e12481d05883b5aa3

* Wed May 01 2024 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-50
- bump v2.3.0-222b36d7bd3a98616eae82993552098747268d5e

* Mon Apr 01 2024 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-49
- bump v2.3.0-16ea5ef0960296d24c945cc3bf2432e525ad5513

* Fri Mar 01 2024 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-48
- bump v2.3.0-653fccf538aa2f2424946f56d39e5de96921c4bb

* Thu Feb 01 2024 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-47
- bump v2.3.0-d90da70f337d04d2ac16051f74bd4c67631879ec

* Mon Jan 01 2024 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-46
- bump v2.3.0-cb0df42a179b640a970aed6987ceac55da5a9917

* Fri Dec 01 2023 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-45
- bump v2.3.0-cec8046d98b74732af007364de312a17abcf52b1

* Wed Nov 01 2023 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-44
- bump v2.3.0-3c43e66be611ff6ddce3836d12df298afa48087b

* Fri Oct 13 2023 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-43
- bump v2.3.0-b311c049d433a421e00bc52c442d47f373b949a1

* Fri Oct 13 2023 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-42
- bump v2.3.0-cb9f500d0

* Fri Oct 13 2023 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-41
- bump v2.3.0-70dd2d888

* Fri Oct 13 2023 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-40
- bump v2.3.0-398ea25c0

* Fri Oct 13 2023 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-39
- bump v2.3.0-832d08880

* Fri Oct 13 2023 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-38
- bump v2.3.0-489165ce6

* Fri Oct 13 2023 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-37
- bump v2.3.0-7d7bfeb3e

* Fri Oct 13 2023 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-36
- bump v2.3.0-41c61d7ab

* Thu Oct 12 2023 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-35
- bump v2.3.0-e041bac7f

* Thu Oct 12 2023 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-34
- bump v2.3.0-9ab3feb4d

* Wed Dec 28 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-33
- do not lock the repository version on Amazon Linux 2022

* Wed Dec 28 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-32
- bump v2.3.0-0f08b675c
- fix minor version problem on Amazon Linux 2022

* Wed Nov 30 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-31
- bump v2.3.0-cb831a4b5

* Wed Nov 30 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-30
- bump v2.3.0-d28b53883

* Tue Nov 29 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-29
- bump v2.3.0-6bc369fcf

* Tue Nov 29 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-28
- bump v2.3.0-98c7c889d

* Tue Nov 29 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-27
- bump v2.3.0-a693dcd76

* Tue Nov 29 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-26
- bump v2.3.0-97d070083

* Tue Nov 29 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-25
- bump v2.3.0-48d602412

* Tue Nov 29 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-24
- bump v2.3.0-6bee46445

* Tue Nov 29 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-23
- bump v2.3.0-b61ef3276

* Tue Nov 29 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-22
- bump v2.3.0-25610ea79

* Tue Nov 29 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-21
- bump v2.3.0-14dd3f9c8

* Tue Nov 29 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-20
- bump v2.3.0-423f47ad3

* Tue Nov 29 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-19
- bump v2.3.0-c1134ea1a

* Tue Nov 29 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-18
- bump v2.3.0-909da44bf

* Tue Nov 29 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-17
- bump v2.3.0-3b2513275

* Tue Nov 29 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-16
- bump v2.3.0-d80d88361

* Tue Nov 29 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-15
- bump v2.3.0-55c379fd5

* Tue Nov 29 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-14
- bump v2.3.0-55c379fd5

* Mon Nov 28 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-13
- bump v2.3.0-2c67005ae

* Mon Nov 28 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-12
- bump v2.3.0-cffe1da8f

* Mon Nov 28 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-11
- bump v2.3.0-0a9ddbd14

* Mon Nov 28 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-10
- bump v2.3.0-ec1090a3

* Mon Nov 28 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-9
- bump v2.3.0-f423c02

* Sat Nov 26 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-8
- bump v2.3.0-0a9ddbd1

* Sat Nov 26 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-7
- bump v2.3.0-b4775b5

* Sat Nov 26 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-6
- bump v2.3.0-bf545b8

* Sat Nov 26 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-5
- bump v2.3.0-7081e14

* Sat Nov 26 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-4
- bump v2.3.0-3007562

* Sat Nov 26 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-3
- bump v2.3.0-8db6ef8

* Sat Nov 26 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-2
- bump v2.3.0-6dfa40b

* Fri Nov 25 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.3.0-1
- bump v2.3.0-beta2 (c451265)

* Thu Nov 24 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.2.6-5
- fix base image of AlmaLinux9 and Rockey Linux9

* Thu Nov 24 2022 ICHINOSE Shogo <shogo82148@gmail.com> - 2.2.6-4
- add AlmaLinux9, Rockey Linux9 and Amazon Linux 2022

* Tue Mar 02 2021 ICHINOSE Shogo <shogo82148@gmail.com> - 2.2.6-3
- fix broken docroot

* Mon Feb 22 2021 ICHINOSE Shogo <shogo82148@gmail.com> - 2.2.6-2
- Bump libuv v1.41.0
- Bump libwslay v1.1.1

* Wed Aug 14 2019 ICHINOSE Shogo <shogo82148@gmail.com> - 2.2.6-1
- This is a bug-fix release of the 2.2 series with following changes from 2.2.5, including a vulnerability fix.
- [security fix][http2] fix HTTP/2 DoS attack vectors CVE-2019-9512 CVE-2019-9514 CVE-2019-9515 #2090 (Kazuho Oku)

* Wed May  1 2019 ICHINOSE Shogo <shogo82148@gmail.com> - 2.2.5-2
- Add amazonlinux2 support

* Fri Jun  1 2018 Tatsushi Demachi <tdemachi@gmail.com> - 2.2.5-1
- Update to 2.2.5
- Add patch for avoid c99 syntax issue at compilation

* Fri Dec 15 2017 Tatsushi Demachi <tdemachi@gmail.com> - 2.2.4-1
- Update to 2.2.4
- Remove patch for fixing mruby behavior because it has been fixed by upstream
  in this version

* Thu Oct 19 2017 Tatsushi Demachi <tdemachi@gmail.com> - 2.2.3-1
- Update to 2.2.3
- Add patch for fixing mruby behavior on 2.2.3

* Sat Apr 29 2017 Tatsushi Demachi <tdemachi@gmail.com> - 2.2.2-1
- Update to 2.2.2

* Sat Apr 29 2017 Tatsushi Demachi <tdemachi@gmail.com> - 2.2.0-2
- Add libuv-devel build dependency to libh2o

* Thu Apr  6 2017 Tatsushi Demachi <tdemachi@gmail.com> - 2.2.0-1
- Update to 2.2.0

* Wed Jan 18 2017 Tatsushi Demachi <tdemachi@gmail.com> - 2.1.0-1
- Update to 2.1.0

* Wed Dec 21 2016 Tatsushi Demachi <tdemachi@gmail.com> - 2.0.5-1
- Update to 2.0.5

* Wed Sep 14 2016 Tatsushi Demachi <tdemachi@gmail.com> - 2.0.4-1
- Update to 2.0.4

* Thu Sep  8 2016 Tatsushi Demachi <tdemachi@gmail.com> - 2.0.3-1
- Update to 2.0.3

* Tue Aug 23 2016 Tatsushi Demachi <tdemachi@gmail.com> - 2.0.2-1
- Update to 2.0.2

* Wed Jul 27 2016 Tatsushi Demachi <tdemachi@gmail.com> - 2.0.1-2
- Remove openssl package dependency from libh2o and libh2o-evloop packages
- Put h2o binary in /usr/sbin directory instead of /usr/bin directory

* Sat Jun 25 2016 Tatsushi Demachi <tdemachi@gmail.com> - 2.0.1-1
- Update to 2.0.1
- Remove patches by upstream fix

* Sat Jun  4 2016 Tatsushi Demachi <tdemachi@gmail.com> - 2.0.0-1
- Update to 2.0.0
- Add patch to avoid c++ header issue caused by libuv 1.4.2 or earlier

* Sat Jun  4 2016 Tatsushi Demachi <tdemachi@gmail.com> - 1.7.3-2
- Rename and split h2o-devel package in libh2o, libh2o-evloop and libh2o-devel
- Stop providing static libraries.
- Fix broken library links
- Fix wrong pkg-config's library paths in x86_64 environment

* Sat May 28 2016 Tatsushi Demachi <tdemachi@gmail.com> - 1.7.3-1
- Update to 1.7.3
- Add tmpfiles.d configuration to fix the issue that PID file's parent
  directory is removed after restarting system
- Change 'ruby' build requires to 'ruby-devel'

* Mon May  9 2016 Tatsushi Demachi <tdemachi@gmail.com> - 1.7.2-1
- Update to 1.7.2

* Mon Mar 14 2016 Tatsushi Demachi <tdemachi@gmail.com> - 1.7.1-1
- Update to 1.7.1
- Add pkgconfig dependency to devel sub package

* Fri Feb  5 2016 Tatsushi Demachi <tdemachi@gmail.com> - 1.7.0-1
- Update to 1.7.0

* Fri Feb  5 2016 Tatsushi Demachi <tdemachi@gmail.com> - 1.6.3-1
- Update to 1.6.3

* Wed Jan 13 2016 Tatsushi Demachi <tdemachi@gmail.com> - 1.6.2-1
- Update to 1.6.2

* Sat Dec 19 2015 Tatsushi Demachi <tdemachi@gmail.com> - 1.6.1-1
- Update to 1.6.1

* Sat Dec  5 2015 Tatsushi Demachi <tdemachi@gmail.com> - 1.6.0-1
- Update to 1.6.0
- Remove patch by upstream fix

* Thu Nov 12 2015 Tatsushi Demachi <tdemachi@gmail.com> - 1.5.4-1
- Update to 1.5.4

* Sat Nov  7 2015 Tatsushi Demachi <tdemachi@gmail.com> - 1.5.3-1
- Update to 1.5.3

* Mon Nov  2 2015 Tatsushi Demachi <tdemachi@gmail.com> - 1.5.2-2
- Add mruby support
- Fix official URL

* Tue Oct 20 2015 Tatsushi Demachi <tdemachi@gmail.com> - 1.5.2-1
- Update to 1.5.2

* Fri Oct  9 2015 Tatsushi Demachi <tdemachi@gmail.com> - 1.5.0-2
- Add patch to fix CMake version issue for CentOS 7 build

* Thu Oct  8 2015 Donald Stufft <donald@stufft.io> - 1.5.0-1
- Update to 1.5.0

* Wed Sep 16 2015 Tatsushi Demachi <tdemachi@gmail.com> - 1.4.5-1
- Update to 1.4.5

* Tue Aug 18 2015 Tatsushi Demachi <tdemachi@gmail.com> - 1.4.4-1
- Update to 1.4.4

* Mon Aug 17 2015 Tatsushi Demachi <tdemachi@gmail.com> - 1.4.3-1
- Update to 1.4.3

* Wed Jul 29 2015 Tatsushi Demachi <tdemachi@gmail.com> - 1.4.2-1
- Update to 1.4.2

* Thu Jul 23 2015 Tatsushi Demachi <tdemachi@gmail.com> - 1.4.1-1
- Update to 1.4.1

* Tue Jun 23 2015 Tatsushi Demachi <tdemachi@gmail.com> - 1.3.1-4
- Add OpenSUSE support

* Mon Jun 22 2015 Tatsushi Demachi <tdemachi@gmail.com> - 1.3.1-3
- Fix logrotate

* Sun Jun 21 2015 Tatsushi Demachi <tdemachi@gmail.com> - 1.3.1-2
- Add fedora support

* Sat Jun 20 2015 Tatsushi Demachi <tdemachi@gmail.com> - 1.3.1-1
- Update to 1.3.1

* Thu Jun 18 2015 Tatsushi Demachi <tdemachi@gmail.com> - 1.3.0-1
- Update to 1.3.0
- Move library and headers to devel sub-package

* Fri May 22 2015 Tatsushi Demachi <tdemachi@gmail.com> - 1.2.0-1
- Initial package release
