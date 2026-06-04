Name:           ats-quant-factor-engine
Version:        0.1.0
Release:        1%{?dist}
Summary:        C++ Factor development framework

License:        Custom
URL:            http://gitlab.htzq.htsc.com.cn/ats-quant-cpp/ats-quant-factor-engine
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  devtoolset-11
Requires:       arrow-devel
Requires:       parquet-devel

%description
factor

%define __requires_exclude libpython3.9.so.1.0
%global debug_package %{nil}

%prep
%setup -q

%build
cmake -B build \
    -S atsfactor \
    -DCMAKE_BUILD_TYPE=Release \
    -DATSFACTOR_ENABLE_TESTING=ON \
    -DCMAKE_INSTALL_PREFIX:PATH=%{_prefix} \
    -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build build -j $(nproc)

cmake -B build-debug \
    -S atsfactor \
    -DCMAKE_BUILD_TYPE=Debug \
    -DATSFACTOR_ENABLE_TESTING=ON
cmake --build build-debug -j $(nproc)

%check
cppcheck --enable=performance \
    --enable=warning \
    --suppressions-list=misc/cppcheck-suppressions-list \
    --project=build/compile_commands.json \
    -j $(nproc) --xml 2>/cppcheck.xml

ln -s ../dataset build-debug/dataset
ctest --test-dir build-debug \
    -j $(nproc) \
    --output-junit /ctest.xml

gcovr -r . --cobertura-pretty --cobertura /coverage.xml 

%install
cd build
%{make_install}

%files
%{_includedir}/huatai/atsquant/factor.h
%{_includedir}/huatai/atsquant/factor
%{_libdir}/atsfactor*
%{_libdir}/cmake/atsfactor

