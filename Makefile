SOURCE_ARCHIVE := 26b116e9536be8cf07036185e3edf9d721c9bac2.tar.gz
WSLAY_VERSION := 1.1.1
WSLAY_SOURCE_ARCHIVE := wslay-$(WSLAY_VERSION).tar.gz
BROTLI_VERSION := 1.1.0
BROTLI_SOURCE_ARCHIVE := brotli-$(BROTLI_VERSION).tar.gz
TARGZ_FILE := h2o.tar.gz
IMAGE_NAME := h2o-package

.PHONY: all
all: amazonlinux2 amazonlinux2023 almalinux8 rockylinux8 almalinux9 rockylinux9

.PHONY: amazonlinux2
amazonlinux2: amazonlinux2.build

.PHONY: amazonlinux2023
amazonlinux2023: amazonlinux2023.build

.PHONY: almalinux8
almalinux8: almalinux8.build

.PHONY: almalinux9
almalinux9: almalinux9.build

.PHONY: rockylinux8
rockylinux8: rockylinux8.build

.PHONY: rockylinux9
rockylinux9: rockylinux9.build

rpmbuild/SOURCES/$(SOURCE_ARCHIVE):
	curl -SL https://github.com/h2o/h2o/archive/$(SOURCE_ARCHIVE) -o rpmbuild/SOURCES/$(SOURCE_ARCHIVE)

rpmbuild/SOURCES/$(WSLAY_SOURCE_ARCHIVE):
	curl -sSL https://github.com/tatsuhiro-t/wslay/releases/download/release-1.1.1/wslay-1.1.1.tar.gz -o rpmbuild/SOURCES/$(WSLAY_SOURCE_ARCHIVE)

rpmbuild/SOURCES/$(BROTLI_SOURCE_ARCHIVE):
	curl -sSL https://github.com/google/brotli/archive/refs/tags/v1.1.0.tar.gz -o rpmbuild/SOURCES/$(BROTLI_SOURCE_ARCHIVE)

%.build: rpmbuild/SPECS/h2o.spec rpmbuild/SOURCES/$(SOURCE_ARCHIVE) \
		rpmbuild/SOURCES/$(WSLAY_SOURCE_ARCHIVE) \
		rpmbuild/SOURCES/$(BROTLI_SOURCE_ARCHIVE) \
		rpmbuild/SOURCES/01-fix-build.patch \
		rpmbuild/SOURCES/h2o.conf \
		rpmbuild/SOURCES/h2o.logrotate rpmbuild/SOURCES/h2o.service \
		rpmbuild/SOURCES/h2o.tmpfiles rpmbuild/SOURCES/index.html
	./scripts/build.sh $*

.PHONY: upload
upload:
	./scripts/upload.pl

.PHONY: test
test: test-amazonlinux2 test-amazonlinux2023 test-almalinux8 test-almalinux9 test-rockylinux8 test-rockylinux9

.PHONY: test-amazonlinux2
test-amazonlinux2:
	./scripts/test.sh amazonlinux2

.PHONY: test-amazonlinux2023
test-amazonlinux2023:
	./scripts/test.sh amazonlinux2023

.PHONY: test-almalinux8
test-almalinux8:
	./scripts/test.sh almalinux8

.PHONY: test-almalinux9
test-almalinux9:
	./scripts/test.sh almalinux9

.PHONY: test-rockylinux8
test-rockylinux8:
	./scripts/test.sh rockylinux8

.PHONY: test-rockylinux9
test-rockylinux9:
	./scripts/test.sh rockylinux9

.PHONY: clean
clean:
	rm -rf *.build.bak *.build bintray
	rm -f rpmbuild/SOURCES/v*.tar.gz
	docker rmi $(IMAGE_NAME)-almalinux8 || true
	docker rmi $(IMAGE_NAME)-almalinux9 || true
	docker rmi $(IMAGE_NAME)-amazonlinux2 || true
	docker rmi $(IMAGE_NAME)-amazonlinux2023 || true
	docker rmi $(IMAGE_NAME)-rockylinux8 || true
	docker rmi $(IMAGE_NAME)-rockylinux9 || true

.PHONY: tag
tag:
	./scripts/tag.sh
