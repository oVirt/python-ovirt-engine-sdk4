#!/bin/bash -xe

# remove any previous artifacts
rm -rf output
rm -f ./*tar.gz

# Create exported-artifacts
[[ -d exported-artifacts ]] || mkdir -p $PWD/exported-artifacts

# Create build

./build.sh dist

# create the src.rpm
rpmbuild \
    -D "_srcrpmdir $PWD/output" \
    -D "_sourcedir $PWD/" \
    -D "_topmdir $PWD/rpmbuild" \
    -bs ./python-ovirt-engine-sdk4.spec

if [[ "$(rpm --eval "%dist")" == ".el8" ]]; then
# create the src.rpm
rpmbuild \
    -D "_srcrpmdir $PWD/output" \
    -D "_sourcedir $PWD/" \
    -D "_topmdir $PWD/rpmbuild" \
    -bs ./python38-ovirt-engine-sdk4.spec
fi

# install any build requirements
dnf builddep output/*src.rpm

# create the rpms
rpmbuild \
    -D "_rpmdir $PWD/output" \
    -D "_topmdir $PWD/rpmbuild" \
    --rebuild  output/*.src.rpm

# Store any relevant artifacts in exported-artifacts for the ci system to
# archive
find output -iname \*rpm -exec mv "{}" exported-artifacts/ \;

# Export build to artifacts
mv ./*tar.gz exported-artifacts/
