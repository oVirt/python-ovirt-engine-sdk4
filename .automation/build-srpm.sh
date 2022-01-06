#!/bin/sh -e

VERSION="4.5.1"
MILESTONE=master
RPM_RELEASE="0.1.${MILESTONE}.$(date -u +%Y%m%d%H%M%S)"

PACKAGE_NAME="python-ovirt-engine-sdk4"

RPM_VERSION=${VERSION}
PACKAGE_VERSION=${VERSION}
[ -n "${MILESTONE}" ] && PACKAGE_VERSION+="_${MILESTONE}"

TARBALL="ovirt-engine-sdk-python-${PACKAGE_VERSION}.tar.gz"


GENERATED_FILES="
 lib/ovirtsdk4/version.py
 setup.py
 PKG-INFO
 lib/ovirt_engine_sdk_python.egg-info/PKG-INFO
 python-ovirt-engine-sdk4.spec
"

for gen_file in ${GENERATED_FILES} ; do
  sed \
    -e "s|@RPM_VERSION@|${RPM_VERSION}|g" \
    -e "s|@RPM_RELEASE@|${RPM_RELEASE}|g" \
    -e "s|@PACKAGE_NAME@|${PACKAGE_NAME}|g" \
    -e "s|@PACKAGE_VERSION@|${PACKAGE_VERSION}|g" \
    < ${gen_file}.in > ${gen_file}
done

find . -not -name '*.spec' -not -name '*.in' -type f | tar --files-from /proc/self/fd/0 -czf "${TARBALL}" python-ovirt-engine-sdk4.spec

# Directory, where build artifacts will be stored, should be passed as the 1st parameter
ARTIFACTS_DIR=${1:-exported-artifacts}

# Prepare source archive
[[ -d rpmbuild ]] || mkdir -p rpmbuild

rpmbuild \
    -D "_topdir rpmbuild" \
    -ts ${TARBALL}
