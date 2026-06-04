cmake_minimum_required(VERSION 3.15)

project(Atsfactor VERSION 0.1.0)
string(TOLOWER ${PROJECT_NAME} PROJECT_NAME_LOWER)

set(ATSFACTOR_ENABLE_TESTING OFF CACHE STRING "enable testing")
set(ATSFACTOR_DEVELOPMENT_MODE ON CACHE STRING "development mode")
set(ATSFACTOR_ENABLE_EXAMPLE OFF CACHE STRING "enable example")
set(ATSFACTOR_LATENCY_TEST OFF CACHE STRING "latency_test")
set(ATSFACTOR_PARALLEL_FRAMEWORK "taskflow" CACHE STRING "parallel framework for factor caculation")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++20 -fopenmp-simd")

set(ATSFACTOR_USE_TASKFLOW 0)
set(ATSFACTOR_USE_OPENMP 0)
if (ATSFACTOR_PARALLEL_FRAMEWORK STREQUAL "taskflow")
  set(ATSFACTOR_USE_TASKFLOW 1)
  add_compile_definitions(ATSFACTOR_USE_TASKFLOW=1)
elseif(ATSFACTOR_PARALLEL_FRAMEWORK STREQUAL "openmp" )
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fopenmp")
  set(ATSFACTOR_USE_OPENMP 1)
  add_compile_definitions(ATSFACTOR_USE_OPENMP=1)
else()
  message(FATAL_ERROR "invalid parallel framework: ${ATSFACTOR_PARALLEL_FRAMEWORK}")
endif()

set(PYBIND11_FINDPYTHON ON)

if (CMAKE_BUILD_TYPE STREQUAL Debug)
  add_compile_options(-fprofile-arcs -ftest-coverage)
  add_link_options(--coverage)
  add_compile_definitions(_DEBUG)
else()
  set(CMAKE_INTERPROCEDURAL_OPTIMIZATION ON)
endif()

include(GNUInstallDirs)
include(GenerateExportHeader)
include(CMakePackageConfigHelpers)
add_compile_definitions(
  FMT_HEADER_ONLY
  PROJECT_NAME_LOWER=${PROJECT_NAME_LOWER}
  PROJECT_VERSION=${PROJECT_VERSION}
)

if (ATSFACTOR_LATENCY_TEST) 
  add_compile_definitions(_LATENCY_TEST)
endif()

find_package(Arrow REQUIRED)
find_package(Parquet REQUIRED)

include_directories(${CMAKE_CURRENT_SOURCE_DIR}/deps/include)

add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/deps/pybind11)

if (ATSFACTOR_DEVELOPMENT_MODE)
  add_compile_definitions(ATSFACTOR_DEVELOPMENT_MODE=1)
endif()

# find pyarrow
execute_process(COMMAND ${CMAKE_SOURCE_DIR}/cmake_pyarrow.py --get-include
    OUTPUT_VARIABLE PYARROW_INCLUDE_DIR
)
string(STRIP "${PYARROW_INCLUDE_DIR}" PYARROW_INCLUDE_DIR)

execute_process(COMMAND ${CMAKE_SOURCE_DIR}/cmake_pyarrow.py --get-library-dirs
    OUTPUT_VARIABLE PYARROW_LINK_DIR
)
string(STRIP "${PYARROW_LINK_DIR}" PYARROW_LINK_DIR)

execute_process(COMMAND ${CMAKE_SOURCE_DIR}/cmake_pyarrow.py --get-libraries
    OUTPUT_VARIABLE PYARROW_LIBS
)
string(STRIP "${PYARROW_LIBS}" PYARROW_LIBS)


# generate factors header file
execute_process(COMMAND ${CMAKE_SOURCE_DIR}/generate_factor_types.py
  --input-dir ${CMAKE_SOURCE_DIR}/include/huatai/atsquant/factor/custom
  --input-dir ${CMAKE_SOURCE_DIR}/include/huatai/atsquant/factor/nonfactor
  --include-dir ${CMAKE_SOURCE_DIR}/include
)
# generate done

aux_source_directory(${CMAKE_CURRENT_SOURCE_DIR}/src SRC_LIST)

pybind11_add_module(${PROJECT_NAME_LOWER} SHARED ${SRC_LIST})

generate_export_header(${PROJECT_NAME_LOWER})

target_include_directories(${PROJECT_NAME_LOWER} PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:${CMAKE_INSTALL_PREFIX}/${CMAKE_INSTALL_INCLUDEDIR}>
  PRIVATE ${PYARROW_INCLUDE_DIR}
)

target_link_directories(${PROJECT_NAME_LOWER} PRIVATE ${PYARROW_LINK_DIR})

target_link_libraries(${PROJECT_NAME_LOWER} PUBLIC
  Arrow::arrow_shared
  Parquet::parquet_shared
  PRIVATE ${PYARROW_LIBS}
)

set_property(TARGET ${PROJECT_NAME_LOWER} PROPERTY VERSION ${PROJECT_VERSION})
set_property(TARGET ${PROJECT_NAME_LOWER} PROPERTY SOVERSION "${PROJECT_VERSION_MAJOR}.${PROJECT_VERSION_MINOR}")

set(PROJECT_EXPORT_NAME ${PROJECT_NAME}Targets)
set(PROJECT_CONFIG_NAME ${PROJECT_NAME}Config)
set(PROJECT_VERSION_NAME ${PROJECT_NAME}Version)
set(INSTALL_CONFIGDIR ${CMAKE_INSTALL_LIBDIR}/cmake/${PROJECT_NAME_LOWER})

install(TARGETS ${PROJECT_NAME_LOWER}
  EXPORT ${PROJECT_EXPORT_NAME}
  DESTINATION "${CMAKE_INSTALL_LIBDIR}"
)
install(DIRECTORY include/huatai/atsquant/factor DESTINATION "${CMAKE_INSTALL_INCLUDEDIR}/huatai/atsquant")
install(FILES include/huatai/atsquant/factor.h DESTINATION "${CMAKE_INSTALL_INCLUDEDIR}/huatai/atsquant")

export(EXPORT ${PROJECT_EXPORT_NAME}
  FILE "${CMAKE_BINARY_DIR}/${PROJECT_EXPORT_NAME}.cmake")
configure_file("${CMAKE_CURRENT_SOURCE_DIR}/cmake/config.cmake"
  "${CMAKE_BINARY_DIR}/${PROJECT_CONFIG_NAME}.cmake"
)
write_basic_package_version_file(
  "${CMAKE_BINARY_DIR}/${PROJECT_VERSION_NAME}.cmake"
  VERSION ${PROJECT_VERSION}
  COMPATIBILITY AnyNewerVersion
)

install(EXPORT ${PROJECT_EXPORT_NAME} FILE ${PROJECT_EXPORT_NAME}.cmake DESTINATION "${INSTALL_CONFIGDIR}")
install(
  FILES 
    "${CMAKE_BINARY_DIR}/${PROJECT_CONFIG_NAME}.cmake"
    "${CMAKE_BINARY_DIR}/${PROJECT_VERSION_NAME}.cmake"
  DESTINATION
    "${INSTALL_CONFIGDIR}"
)

# test
if (ATSFACTOR_ENABLE_TESTING)
  enable_testing()
  find_package(GTest REQUIRED)
  aux_source_directory(${CMAKE_CURRENT_SOURCE_DIR}/test TEST_LIST)
  add_executable(${PROJECT_NAME_LOWER}_test ${TEST_LIST})
  target_link_libraries(${PROJECT_NAME_LOWER}_test GTest::gtest_main ${PROJECT_NAME_LOWER})
  include(GoogleTest)
  gtest_discover_tests(${PROJECT_NAME_LOWER}_test)
endif()

# example
if (ATSFACTOR_ENABLE_EXAMPLE)
  aux_source_directory(${CMAKE_CURRENT_SOURCE_DIR}/example EXAMPLE_LIST)
  add_executable(${PROJECT_NAME_LOWER}_example ${EXAMPLE_LIST})
  target_link_libraries(${PROJECT_NAME_LOWER}_example ${PROJECT_NAME_LOWER})
endif()