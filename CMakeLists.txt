# fable2 - ReXGlue Recompiled Project
#
# SDK boilerplate lives in generated/rexglue.cmake.

cmake_minimum_required(VERSION 3.25)
project(fable2 LANGUAGES CXX)

option(REXGLUE_ENABLE_FAULT_WALK
    "Enable experimental FULL generated-function fault walking"
    OFF)
option(REXGLUE_ENABLE_FAULT_WALK_DISPATCH
    "Enable lightweight invalid/unregistered-dispatch fault walking"
    OFF)

if(REXGLUE_ENABLE_FAULT_WALK AND REXGLUE_ENABLE_FAULT_WALK_DISPATCH)
    message(FATAL_ERROR
        "Choose only one fault-walk mode: FULL or DISPATCH_ONLY")
endif()

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(generated/rexglue.cmake)

set(FABLE2_REXGLUE_VERSION_STRING "0.10.0.7-dev.g5a7ceb6")
if(NOT REXGLUE_VERSION_STRING STREQUAL FABLE2_REXGLUE_VERSION_STRING)
    message(FATAL_ERROR
        "Fable II requires audited ReXGlue ${FABLE2_REXGLUE_VERSION_STRING}; "
        "found ${REXGLUE_VERSION_STRING}")
endif()

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
    if(TARGET fable2_recomp)
        target_compile_definitions(fable2_recomp PRIVATE
            REXGLUE_ENABLE_FAULT_WALK=1)
    endif()
elseif(REXGLUE_ENABLE_FAULT_WALK_DISPATCH)
    target_compile_definitions(fable2 PRIVATE
        REXGLUE_ENABLE_FAULT_WALK_DISPATCH=1)
endif()
