#!/bin/bash

source /etc/profile

set -ex

SOURCE_DIR=$(realpath $(dirname $0)/..)
DIST_DIR=${SOURCE_DIR}/dist

rpmdev-setuptree
cd /
tar --exclude-vcs --exclude="*.rpm" --exclude="tmp" -czf ${PKG_NAME}-${PKG_VER}{.tar.gz,}
mv ${PKG_NAME}-${PKG_VER}.tar.gz ${HOME}/rpmbuild/SOURCES/
cp ${SOURCE_DIR}/misc/${PKG_NAME}.spec ${HOME}/rpmbuild/SPECS/${PKG_NAME}.spec
rpmbuild -ba ${HOME}/rpmbuild/SPECS/${PKG_NAME}.spec
mkdir -p ${SOURCE_DIR}/dist
cp -f ${HOME}/rpmbuild/RPMS/x86_64/* ${SOURCE_DIR}/dist/
cp -f /*.xml ${SOURCE_DIR}/dist/