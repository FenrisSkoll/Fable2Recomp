cmake_minimum_required(VERSION 3.25)
project(fable2_xex_provenance LANGUAGES CXX)
find_package(rexglue CONFIG REQUIRED)
add_executable(fable2_xex_provenance main.cpp)
target_compile_features(fable2_xex_provenance PRIVATE cxx_std_23)
target_link_libraries(fable2_xex_provenance PRIVATE rex::runtime)
add_custom_command(TARGET fable2_xex_provenance POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        $<TARGET_RUNTIME_DLLS:fable2_xex_provenance>
        $<TARGET_FILE_DIR:fable2_xex_provenance>
    COMMAND_EXPAND_LISTS)
