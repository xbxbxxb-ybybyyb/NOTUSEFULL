cmake_minimum_required(VERSION 3.12)

project(XdbFramework VERSION 0.1.0)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)



include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/thirdparty/zstd/lib/compress)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/thirdparty)

aux_source_directory(${CMAKE_CURRENT_SOURCE_DIR}/src common_src)
add_subdirectory(thirdparty/zstd/build/cmake zstd)
link_directories("/data/group/800002/c++framework/arrow/9.0.0/lib64/")

add_library(xdb STATIC ${common_src})
target_link_libraries(xdb zstd)


