PROJECT_DIR := atsfactor
DESTDIR ?= /usr/local
BINARY_DIR ?= build
JOBS ?= 8
BUILD_TYPE ?= Release
ENABLE_TESTING ?= OFF
ENABLE_EXAMPLE ?= OFF
CMAKE_CONFIGURE_ARGS += \
	-DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
	-DCMAKE_BUILD_TYPE=$(BUILD_TYPE) \
	-DCMAKE_INSTALL_PREFIX=$(DESTDIR) \
	-DATSFACTOR_ENABLE_TESTING=$(ENABLE_TESTING) \
	-DATSFACTOR_ENABLE_EXAMPLE=$(ENABLE_EXAMPLE)

.PHONY: all configure build install clean

all:
	make configure
	make build

configure:
	mkdir -p $(BINARY_DIR)
	cmake -S$(PROJECT_DIR) -B$(BINARY_DIR) $(CMAKE_CONFIGURE_ARGS)

build:
	cmake --build $(BINARY_DIR) -j$(JOBS)

install:
	cmake --install $(BINARY_DIR)
	
clean:
	rm -rf $(BINARY_DIR)
	
_pkg_name := ats-quant-factor-engine
_pkg_ver := 0.1.0
rpm:
	cp misc/${_pkg_name}.spec ${HOME}/rpmbuild/SPECS/${_pkg_name}.spec
	cd ${HOME}/rpmbuild/SOURCES && \
	rm -rf ${_pkg_name}-${_pkg_ver} && \
	git clone git@gitlab.htzq.htsc.com.cn:ats-quant-cpp/${_pkg_name}.git ${_pkg_name}-${_pkg_ver} && \
	tar --exclude-vcs -czf ${_pkg_name}-${_pkg_ver}{.tar.gz,} && \
	rpmbuild -ba ${HOME}/rpmbuild/SPECS/${_pkg_name}.spec
	