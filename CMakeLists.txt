# fable2 - ReXGlue Recompiled Project
#
# SDK boilerplate lives in generated/rexglue.cmake.

cmake_minimum_required(VERSION 3.25)
project(fable2 LANGUAGES CXX)

option(REXGLUE_ENABLE_FAULT_WALK
    "Enable experimental diagnostic generated-function fault walking"
    OFF)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(generated/rexglue.cmake)

# Sources
set(FABLE2_SOURCES
    src/main.cpp
)

if(WIN32)
    add_executable(fable2 WIN32 ${FABLE2_SOURCES})
else()
    add_executable(fable2 ${FABLE2_SOURCES})
endif()

rexglue_setup_target(fable2 GPU_PLUGINS xenos)

if(REXGLUE_ENABLE_FAULT_WALK)
    if(NOT WIN32)
        message(FATAL_ERROR "REXGLUE_ENABLE_FAULT_WALK v1 requires Windows SEH")
    endif()
    target_compile_definitions(fable2 PRIVATE REXGLUE_ENABLE_FAULT_WALK=1)
endif()
