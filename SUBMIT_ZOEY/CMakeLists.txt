CMAKE_MINIMUM_REQUIRED(VERSION 3.7)                                                       
PROJECT(TAKEHOME)

set(CMAKE_CXX_FLAGS "-std=c++11 -fPIC -Wall -Wextra -fopenmp -O3 -Wno-unused-parameter ")
#set(CMAKE_CXX_FLAGS_DEBUG "-O0 -gdwarf-2 -g3")
                                                                                          
############################################################                              
include_directories("${CMAKE_CURRENT_SOURCE_DIR}")


FILE(GLOB SRC_DIR_LIST "SRC/framework/*.cc")
message("SRC_DIR_LIST=${SRC_DIR_LIST}")
message("${CMAKE_CURRENT_SOURCE_DIR}")
add_library(framework SHARED ${SRC_DIR_LIST})
target_link_libraries(framework  stdc++fs)



FILE(GLOB MAIN1 "SRC/main1.cpp")
add_executable(EXE1 ${MAIN1})
target_link_libraries(EXE1 pthread dl framework)

FILE(GLOB MAIN2 "SRC/main2.cpp")
add_executable(EXE2 ${MAIN2})
target_link_libraries(EXE2 pthread dl framework)


FILE(GLOB MAIN3 "SRC/main3.cpp")
add_executable(EXE3 ${MAIN3})
target_link_libraries(EXE3 pthread dl framework)

FILE(GLOB MAIN4 "SRC/main4.cpp")
add_executable(EXE4 ${MAIN4})
target_link_libraries(EXE4 pthread dl framework)

FILE(GLOB MAIN4 "SRC/main5.cpp")
add_executable(EXE5 ${MAIN4})
target_link_libraries(EXE5 pthread dl framework)
