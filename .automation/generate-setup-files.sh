#!/bin/sh -e

VERSION="4.6.1"
# MILESTONE=master
MILESTONE=
# RPM_RELEASE="0.1.$MILESTONE.$(date -u +%Y%m%d%H%M%S)"
RPM_RELEASE=1

PACKAGE_NAME="python-ovirt-engine-sdk4"

RPM_VERSION=${VERSION}
PACKAGE_VERSION=${VERSION}
[ -n "${MILESTONE}" ] && PACKAGE_VERSION+="_${MILESTONE}"

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

