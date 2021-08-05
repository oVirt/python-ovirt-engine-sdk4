#!/bin/bash

VERSION="4.4.15"
MILESTONE=
RPM_RELEASE="1"

PACKAGE_NAME="python-ovirt-engine-sdk4"

RPM_VERSION=$VERSION
PACKAGE_VERSION=$VERSION
[ -n "$MILESTONE" ] && PACKAGE_VERSION+="_$MILESTONE"
DISPLAY_VERSION=$PACKAGE$VERSION

TARBALL="ovirt-engine-sdk-python-$PACKAGE_VERSION.tar.gz"


dist() {
  echo "Creating tar archive '$TARBALL' ... "
  sed \
   -e "s|@RPM_VERSION@|$RPM_VERSION|g" \
   -e "s|@RPM_RELEASE@|$RPM_RELEASE|g" \
   -e "s|@PACKAGE_NAME@|$PACKAGE_NAME|g" \
   -e "s|@PACKAGE_VERSION@|$PACKAGE_VERSION|g" \
   < python-ovirt-engine-sdk4.spec.in > python-ovirt-engine-sdk4.spec

  find ./* -not -name '*.spec' -not -name 'mocker-*' -not -name 'ci_build_summary.html' -type f | tar --files-from /proc/self/fd/0 -czf "$TARBALL" python-ovirt-engine-sdk4.spec
  echo "tar archive '$TARBALL' created."
}

$1
