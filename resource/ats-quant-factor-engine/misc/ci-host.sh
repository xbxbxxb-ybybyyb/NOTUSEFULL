#!/bin/bash

set -ex

SOURCE_DIR=$(realpath $(dirname $0)/..)
PKG_NAME="ats-quant-factor-engine"
PKG_VER="0.1.0"

# ssh private key
#SSH_SK_PATH=${SOURCE_DIR}/tmp/id_ed25519
#mkdir -p ${SOURCE_DIR}/tmp
#cp -f $HOME/.ssh/id_ed25519 ${SSH_SK_PATH}
#sudo chown root:root ${SSH_SK_PATH}
#sudo chmod 600 ${SSH_SK_PATH}

docker run --rm \
    --network host \
    -v ${SOURCE_DIR}:/${PKG_NAME}-${PKG_VER} \
    -e PKG_NAME=${PKG_NAME} \
    -e PKG_VER=${PKG_VER} \
    localhost/ats-quant-cpp-dev:latest \
    /${PKG_NAME}-${PKG_VER}/misc/ci-container.sh

sudo rm -rf ${SOURCE_DIR}/tmp
sudo chown -R 1000:1000 ${SOURCE_DIR}/dist
