#!/bin/sh -e

VERSION="4.5.3"
MILESTONE=master
RPM_RELEASE="0.1.$MILESTONE.$(date -u +%Y%m%d%H%M%S)"

PACKAGE_NAME="python-ovirt-engine-sdk4"

RPM_VERSION=${VERSION}
PACKAGE_VERSION=${VERSION}
[ -n "${MILESTONE}" ] && PACKAGE_VERSION+="_${MILESTONE}"

TARBALL="ovirt-engine-sdk-python-${PACKAGE_VERSION}.tar.gz"

# Set correct python version based on ansible-core.
if [ -z "${ANSIBLE_PYTHON_BIN}" ]; then
  dnf install -y ansible-core
  ANSIBLE_PYTHON_BIN=$(rpm -q --requires ansible-core | grep /usr/bin/python)
fi
ANSIBLE_PYTHON_RPM=$(rpm -q --qf '%{NAME}' -f "${ANSIBLE_PYTHON_BIN}")
ANSIBLE_PYTHON_MAJOR_DOT_MINOR=$(rpm -q --requires ansible-core | sed -n 's/python(abi) = //p')
ANSIBLE_PYTHON_MAJOR_MINOR=$(echo "${ANSIBLE_PYTHON_MAJOR_DOT_MINOR}" | tr -d .)

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
    -e "s|@ANSIBLE_PYTHON_BIN@|${ANSIBLE_PYTHON_BIN}|g" \
    -e "s|@ANSIBLE_PYTHON_RPM@|${ANSIBLE_PYTHON_RPM}|g" \
    -e "s|@ANSIBLE_PYTHON_MAJOR_DOT_MINOR@|${ANSIBLE_PYTHON_MAJOR_DOT_MINOR}|g" \
    -e "s|@ANSIBLE_PYTHON_MAJOR_MINOR@|${ANSIBLE_PYTHON_MAJOR_MINOR}|g" \
    < ${gen_file}.in > ${gen_file}
done

find . -not -name '*.spec' -not -name '*.in' -not -name '*.tar.gz' -type f | tar --files-from /proc/self/fd/0 -czf "${TARBALL}" python-ovirt-engine-sdk4.spec

# Directory, where build artifacts will be stored, should be passed as the 1st parameter
ARTIFACTS_DIR=${1:-exported-artifacts}

# Prepare source archive
[[ -d rpmbuild ]] || mkdir -p rpmbuild

rpmbuild \
    -D "_topdir rpmbuild" \
    -ts ${TARBALL}
