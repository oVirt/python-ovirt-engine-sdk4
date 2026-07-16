#!/bin/sh -e

# Default version - can be overridden via RPM_VERSION env var
DEFAULT_VERSION="4.6.4"

PACKAGE_NAME="python-ovirt-engine-sdk4"

# Use RPM_VERSION from environment if set (e.g., from git tag), otherwise use default
RPM_VERSION="${RPM_VERSION:-${DEFAULT_VERSION}}"

# Use PACKAGE_RPM_RELEASE from environment if set (e.g., from git tag), otherwise default
RPM_RELEASE="${PACKAGE_RPM_RELEASE:-0.master}"

PACKAGE_VERSION="${RPM_VERSION}"

GENERATED_FILES="
 lib/ovirtsdk4/version.py
 setup.py
 PKG-INFO
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

