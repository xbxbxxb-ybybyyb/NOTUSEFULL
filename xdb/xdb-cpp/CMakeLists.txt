cmake_minimum_required(VERSION 3.12)

project(test)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

message(">>>> ${CMAKE_CURRENT_SOURCE_DIR}")
include_directories("/usr/local/lib/boost/include")

add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/xdb)
link_directories("/data/group/800002/c++framework/arrow/9.0.0/lib64/")

add_executable(main main.cpp)
target_link_libraries(main xdb)
