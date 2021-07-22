#!/bin/bash -xe

ROOT_PATH=$PWD

# remove any previous artifacts
rm -rf ./*tar.gz $ROOT_PATH/exported-artifacts $ROOT_PATH/rpmbuild

# Create exported-artifacts
[[ -d exported-artifacts ]] || mkdir -p $ROOT_PATH/exported-artifacts

# Create build

./build.sh build

# create the src.rpm
rpmbuild \
    -D "_srcrpmdir $ROOT_PATH/output" \
    -D "_topmdir $ROOT_PATH/rpmbuild" \
    -D "_builddir $ROOT_PATH/" \
    -ts ./*.gz

# install any build requirements
yum-builddep $ROOT_PATH/output/*src.rpm

# create the rpms
rpmbuild \
    -D "_rpmdir $ROOT_PATH/output" \
    -D "_topmdir $ROOT_PATH/rpmbuild" \
    -D "_builddir $ROOT_PATH/" \
    --rebuild  $ROOT_PATH/output/*.src.rpm

# Store any relevant artifacts in exported-artifacts for the ci system to
# archive
find $ROOT_PATH/output -iname \*rpm -exec mv "{}" $ROOT_PATH/exported-artifacts/ \;

# Export build to artifacts
mv $ROOT_PATH/*tar.gz $ROOT_PATH/exported-artifacts/

cd $ROOT_PATH
