# H2O Unofficial RPM package builder

[![build](https://github.com/shogo82148/h2o-rpm/actions/workflows/build.yml/badge.svg)](https://github.com/shogo82148/h2o-rpm/actions/workflows/build.yml)

This provides [H2O](https://h2o.examp1e.net/) RPM spec file and required files
e.g. systemd service etc. to build RPM.

## How to use prebuilt RPM

Once the file is correctly saved, you can install packages in the repository by

```bash
yum install h2o
```

### Amazon Linux 2023

Install the RPM package for configure the repository.

```shell
dnf install https://shogo82148-rpm-repository.s3.ap-northeast-1.amazonaws.com/amazonlinux/2023/noarch/shogo82148/shogo82148-1.0.9-1.amzn2023.noarch.rpm
```

### AlmaLinux 8, 9 and 10

AlmaLinux 10:

```shell
dnf install https://shogo82148-rpm-repository.s3.ap-northeast-1.amazonaws.com/almalinux/10/noarch/shogo82148/shogo82148-1.0.9-1.el10.noarch.rpm
```

AlmaLinux 9:

```shell
dnf install https://shogo82148-rpm-repository.s3.ap-northeast-1.amazonaws.com/almalinux/9/noarch/shogo82148/shogo82148-1.0.9-1.el9.noarch.rpm
```

AlmaLinux 8:

```shell
yum install https://shogo82148-rpm-repository.s3.ap-northeast-1.amazonaws.com/almalinux/8/noarch/shogo82148/shogo82148-1.0.9-1.el8.noarch.rpm
```

### Rocky Linux 8, 9 and 10

Rocky Linux 10:

```shell
dnf install https://shogo82148-rpm-repository.s3.ap-northeast-1.amazonaws.com/rockylinux/10/noarch/shogo82148/shogo82148-1.0.9-1.el10.noarch.rpm
```

Rocky Linux 9:

```shell
dnf install https://shogo82148-rpm-repository.s3.ap-northeast-1.amazonaws.com/rockylinux/9/noarch/shogo82148/shogo82148-1.0.9-1.el9.noarch.rpm
```

Rocky Linux 8:

```shell
yum install https://shogo82148-rpm-repository.s3.ap-northeast-1.amazonaws.com/rockylinux/8/noarch/shogo82148/shogo82148-1.0.9-1.el8.noarch.rpm
```

## License

This is under MIT License. Please see the
[LICENSE](https://github.com/shogo82148/h2o-rpm/blob/master/LICENSE) file for
details.
