// Load-only provenance probe. Never prepares or launches guest execution.
// Output contains private executable bytes; keep it outside tracked evidence.
#include <rex/kernel/init.h>
#include <rex/runtime.h>
#include <rex/system/user_module.h>
#include <rex/system/xex_module.h>

#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <cstddef>
#include <rex/system/util/xex2_info.h>

#ifdef _WIN32
#include <windows.h>
#endif

int main(int argc, char** argv) {
  try {
    if (argc != 5 && argc != 6) {
      std::cerr << "Usage: fable2_xex_provenance <tool|runtime> <game-root> "
                   "<guest-xex-path> <new-output-directory> [update-root]\n";
      return 2;
    }
    const std::string mode = argv[1];
    if (mode != "tool" && mode != "runtime") {
      throw std::runtime_error("Mode must be tool or runtime");
    }
    const auto game = std::filesystem::canonical(argv[2]);
    const std::filesystem::path output = std::filesystem::absolute(argv[4]);
    if (!std::filesystem::is_directory(game) ||
        !std::filesystem::create_directory(output)) {
      throw std::runtime_error("Game root must exist; output directory must be new");
    }
    const std::filesystem::path update = argc == 6 ? argv[5] : "";
    rex::Runtime runtime(game, output / "user", update, output / "cache",
                         output / "metadata");
    auto status = runtime.Setup(rex::RuntimeConfig{
        .kernel_init = rex::kernel::InitializeKernel,
        .tool_mode = mode == "tool",
    });
    if (status != 0) {
      throw std::runtime_error("Runtime::Setup failed: " + std::to_string(status));
    }
    status = runtime.LoadXexImage(argv[3]);
    if (status != 0) {
      throw std::runtime_error("Runtime::LoadXexImage failed: " + std::to_string(status));
    }
    const auto executable = runtime.kernel_state()->GetExecutableModule();
    const auto* module = executable ? executable->xex_module() : nullptr;
    if (!module || !module->image_size()) {
      throw std::runtime_error("Loaded XEX image is absent");
    }
    std::ofstream metadata(output / "sections.tsv");
    metadata.exceptions(std::ios::badbit | std::ios::failbit);
    metadata << "name\taddress\tsize\texecutable\twritable\n";
    for (const auto& section : module->binary_sections()) {
      metadata << section.name << '\t' << section.virtual_address << '\t'
               << section.virtual_size << '\t' << section.executable << '\t'
               << section.writable << '\n';
    }
    metadata.close();
    std::ofstream image(output / "image.bin", std::ios::binary);
    image.exceptions(std::ios::badbit | std::ios::failbit);
    image.write(reinterpret_cast<const char*>(
                    runtime.memory()->TranslateVirtual(module->base_address())),
                module->image_size());
    image.close();
    // Private loaded headers support controlled delta fixtures without exposing keys
    // or changing loader behavior. Keep this alongside the private image snapshot.
    std::ofstream headers(output / "headers.bin", std::ios::binary);
    headers.exceptions(std::ios::badbit | std::ios::failbit);
    headers.write(reinterpret_cast<const char*>(module->xex_header()),
                  module->xex_header()->header_size);
    headers.close();
    std::ofstream identity(output / "identity.tsv");
    identity.exceptions(std::ios::badbit | std::ios::failbit);
    identity << "mode\tbase\tsize\tentry\n" << mode << '\t'
             << module->base_address() << '\t' << module->image_size() << '\t'
             << module->entry_point() << '\n';
    identity.close();
    std::ofstream layout(output / "layout.tsv");
    layout.exceptions(std::ios::badbit | std::ios::failbit);
    layout << "encryption_bytes\tcompression_bytes\tcompression_info_offset\n"
           << sizeof(rex::be<rex::xex2_encryption_type>) << '\t'
           << sizeof(rex::be<rex::xex2_compression_type>) << '\t'
           << offsetof(rex::xex2_opt_file_format_info, compression_info) << '\n';
    layout.close();
#ifdef _WIN32
    wchar_t module_path[32768]{};
    const auto loaded = GetModuleHandleW(L"rexruntime.dll");
    if (!loaded || !GetModuleFileNameW(loaded, module_path, 32768)) {
      throw std::runtime_error("Could not identify loaded rexruntime.dll");
    }
    std::ofstream module_identity(output / "runtime-module.txt");
    module_identity.exceptions(std::ios::badbit | std::ios::failbit);
    module_identity << std::filesystem::path(module_path).string() << '\n';
    module_identity.close();
#endif
    std::cout << "PASS: loaded without executing guest instructions\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "FAIL: " << error.what() << '\n';
    return 1;
  }
}
