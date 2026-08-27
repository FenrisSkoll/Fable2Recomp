#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>

#include <dis-asm.h>
#include <ppc.h>

namespace {

constexpr uintptr_t kXenonDialect = 0x1 | 0x4 | 0x4000 | 0x8000000 | 0x200 | 0x1000000 | 0x10000;

uint32_t ParseAddress(const char* text) {
  char* end = nullptr;
  const auto value = std::strtoull(text, &end, 0);
  if (end == text || *end != '\0' || value > UINT32_MAX) {
    throw std::runtime_error(std::string("Invalid 32-bit address: ") + text);
  }
  return static_cast<uint32_t>(value);
}

}  // namespace

int main(int argc, char** argv) {
  if (argc != 5) {
    std::cerr << "Usage: ppc-disasm <dump> <dump-guest-base> <start> <exclusive-end>\n";
    return 2;
  }

  try {
    const uint32_t dump_base = ParseAddress(argv[2]);
    const uint32_t start = ParseAddress(argv[3]);
    const uint32_t end = ParseAddress(argv[4]);
    if (start < dump_base || end < start || ((start | end) & 3) != 0) {
      throw std::runtime_error("The requested aligned range is outside the dump");
    }

    std::ifstream input(argv[1], std::ios::binary | std::ios::ate);
    if (!input) {
      throw std::runtime_error(std::string("Could not open dump: ") + argv[1]);
    }
    const auto file_size = static_cast<uint64_t>(input.tellg());
    const uint64_t first_offset = static_cast<uint64_t>(start) - dump_base;
    const uint64_t byte_count = static_cast<uint64_t>(end) - start;
    if (first_offset + byte_count > file_size) {
      throw std::runtime_error("The requested range extends beyond the dump");
    }

    std::vector<uint8_t> bytes(static_cast<size_t>(byte_count));
    input.seekg(static_cast<std::streamoff>(first_offset));
    input.read(reinterpret_cast<char*>(bytes.data()), static_cast<std::streamsize>(bytes.size()));
    if (!input && !bytes.empty()) {
      throw std::runtime_error("Could not read the requested range");
    }

    disassemble_info info{};
    INIT_DISASSEMBLE_INFO(info, stdout, fprintf);
    info.arch = bfd_arch_powerpc;
    info.endian = BFD_ENDIAN_BIG;
    info.private_data = reinterpret_cast<void*>(kXenonDialect);

    for (uint32_t address = start; address < end; address += 4) {
      const auto offset = static_cast<size_t>(address - start);
      ppc_insn instruction{};
      info.buffer = bytes.data() + offset;
      info.buffer_vma = address;
      info.buffer_length = 4;
      const int decoded = decode_insn_ppc(address, &info, &instruction);

      const uint32_t raw = (static_cast<uint32_t>(bytes[offset]) << 24) |
                           (static_cast<uint32_t>(bytes[offset + 1]) << 16) |
                           (static_cast<uint32_t>(bytes[offset + 2]) << 8) |
                           static_cast<uint32_t>(bytes[offset + 3]);
      std::cout << "0x" << std::uppercase << std::hex << std::setw(8) << std::setfill('0')
                << address << ": " << std::setw(8) << raw << "  ";
      if (decoded == 4 && instruction.opcode != nullptr) {
        std::cout << instruction.opcode->name;
        if (instruction.op_str[0] != '\0') {
          std::cout << " " << instruction.op_str;
        }
      } else {
        std::cout << ".long 0x" << std::setw(8) << raw;
      }
      std::cout << '\n';
    }
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }

  return 0;
}
