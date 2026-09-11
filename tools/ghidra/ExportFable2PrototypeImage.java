// Export initialized bytes and deterministic metadata from a prototype XEX.
// @category Fable2
// @runtime Java

import java.io.BufferedWriter;
import java.io.IOException;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Base64;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

import ghidra.app.script.GhidraScript;
import ghidra.framework.Application;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;

public class ExportFable2PrototypeImage extends GhidraScript {
    private static final String SCHEMA_NAME = "fable2-prototype-derived-image";
    private static final long SCHEMA_VERSION = 1;
    private static final String EXPORTER_VERSION = "1.0.0";
    private static final int BUFFER_SIZE = 1024 * 1024;

    @Override
    protected void run() throws Exception {
        if (currentProgram == null) {
            throw new IllegalStateException("No Ghidra program is open");
        }

        Map<String, String> arguments = parseArguments(getScriptArgs());
        Path outputDirectory = requiredDirectory(arguments, "output-directory");
        Files.createDirectories(outputDirectory);
        Path sectionsDirectory = outputDirectory.resolve("sections");
        Files.createDirectories(sectionsDirectory);

        if (!currentProgram.getLanguage().isBigEndian()) {
            throw new IllegalStateException("Prototype export requires a big-endian program");
        }

        Memory memory = currentProgram.getMemory();
        List<MemoryBlock> blocks = new ArrayList<>(Arrays.asList(memory.getBlocks()));
        blocks.sort(Comparator
            .comparingLong((MemoryBlock block) -> unsignedOffset(block.getStart()))
            .thenComparing(MemoryBlock::getName));

        List<Map<String, Object>> blockRecords = new ArrayList<>();
        int ordinal = 0;
        for (MemoryBlock block : blocks) {
            monitor.checkCancelled();
            blockRecords.add(exportBlock(block, sectionsDirectory, ordinal++));
        }

        List<Map<String, Object>> functions = new ArrayList<>();
        FunctionIterator functionIterator = currentProgram.getFunctionManager().getFunctions(true);
        while (functionIterator.hasNext()) {
            Function function = functionIterator.next();
            functions.add(orderedMap(
                "entry", hex(unsignedOffset(function.getEntryPoint())),
                "name", function.getName(),
                "is_external", function.isExternal(),
                "body_min", hex(unsignedOffset(function.getBody().getMinAddress())),
                "body_max_inclusive", hex(unsignedOffset(function.getBody().getMaxAddress())),
                "body_size", function.getBody().getNumAddresses()));
        }

        List<Map<String, Object>> symbols = new ArrayList<>();
        SymbolIterator symbolIterator = currentProgram.getSymbolTable().getAllSymbols(true);
        while (symbolIterator.hasNext()) {
            Symbol symbol = symbolIterator.next();
            if (!symbol.isExternal()) {
                continue;
            }
            Address address = symbol.getAddress();
            symbols.add(orderedMap(
                "address", address == null ? null : hex(unsignedOffset(address)),
                "name", symbol.getName(true),
                "type", symbol.getSymbolType().toString(),
                "is_external", symbol.isExternal(),
                "is_primary", symbol.isPrimary()));
        }
        symbols.sort(Comparator
            .comparing((Map<String, Object> record) -> String.valueOf(record.get("address")))
            .thenComparing(record -> String.valueOf(record.get("name"))));

        Map<String, Object> root = new LinkedHashMap<>();
        root.put("schema", orderedMap("name", SCHEMA_NAME, "version", SCHEMA_VERSION));
        root.put("exporter", orderedMap(
            "name", "ExportFable2PrototypeImage.java",
            "version", EXPORTER_VERSION,
            "commit", arguments.getOrDefault("exporter-commit", "unknown")));
        root.put("source", orderedMap(
            "build_id", arguments.get("build-id"),
            "relative_path", decodeBase64(arguments.get("relative-path-base64")),
            "sha256", arguments.get("source-sha256"),
            "size", parseUnsignedDecimal(arguments.get("source-size")),
            "title_update_sha256", emptyToNull(arguments.get("title-update-sha256")),
            "title_update_size", parseOptionalUnsignedDecimal(
                arguments.get("title-update-size"))));
        root.put("toolchain", orderedMap(
            "ghidra_version", Application.getApplicationVersion(),
            "xexloader", arguments.getOrDefault("xexloader-version", "unknown"),
            "loader_name", currentProgram.getExecutableFormat(),
            "language_id", currentProgram.getLanguageID().getIdAsString(),
            "processor", currentProgram.getLanguage().getProcessor().toString(),
            "compiler_spec", currentProgram.getCompilerSpec()
                .getCompilerSpecID().getIdAsString()));
        root.put("program", orderedMap(
            "domain_path", currentProgram.getDomainFile().getPathname(),
            "name", currentProgram.getName(),
            "executable_sha256", currentProgram.getExecutableSHA256(),
            "image_base", hex(determineImageBase(blocks)),
            "entry_point", currentProgram.getSymbolTable().getExternalEntryPointIterator().hasNext()
                ? hex(unsignedOffset(currentProgram.getSymbolTable()
                    .getExternalEntryPointIterator().next()))
                : null,
            "min_address", hex(unsignedOffset(memory.getMinAddress())),
            "max_address_inclusive", hex(unsignedOffset(memory.getMaxAddress())),
            "big_endian", currentProgram.getLanguage().isBigEndian(),
            "memory_block_count", (long) blockRecords.size(),
            "function_count", (long) functions.size(),
            "symbol_count", (long) symbols.size()));
        root.put("memory_blocks", blockRecords);
        root.put("functions", functions);
        root.put("symbols", symbols);

        writeJsonAtomically(outputDirectory.resolve("derived-image.json"), root);
        println("Exported prototype image to " + outputDirectory);
    }

    private Map<String, Object> exportBlock(
            MemoryBlock block, Path sectionsDirectory, int ordinal) throws Exception {
        long start = unsignedOffset(block.getStart());
        long length = block.getSize();
        String relativePath = null;
        String digest = null;

        if (block.isInitialized()) {
            String filename = String.format(Locale.ROOT, "%02d-%s-%08X.bin",
                ordinal, sanitize(block.getName()), start);
            Path output = sectionsDirectory.resolve(filename);
            MessageDigest sha256 = MessageDigest.getInstance("SHA-256");
            byte[] buffer = new byte[BUFFER_SIZE];
            Address cursor = block.getStart();
            long remaining = length;
            Path temporary = output.resolveSibling(output.getFileName() + ".tmp");
            try (OutputStream stream = Files.newOutputStream(temporary)) {
                while (remaining > 0) {
                    monitor.checkCancelled();
                    int count = (int)Math.min(buffer.length, remaining);
                    int read = currentProgram.getMemory().getBytes(cursor, buffer, 0, count);
                    if (read <= 0) {
                        throw new IOException("Unable to read block " + block.getName());
                    }
                    stream.write(buffer, 0, read);
                    sha256.update(buffer, 0, read);
                    cursor = cursor.add(read);
                    remaining -= read;
                }
            }
            Files.move(temporary, output,
                java.nio.file.StandardCopyOption.REPLACE_EXISTING,
                java.nio.file.StandardCopyOption.ATOMIC_MOVE);
            relativePath = "sections/" + filename;
            digest = hexDigest(sha256.digest());
        }

        return orderedMap(
            "name", block.getName(),
            "start", hex(start),
            "end_exclusive", hex(start + length),
            "size", length,
            "read", block.isRead(),
            "write", block.isWrite(),
            "execute", block.isExecute(),
            "initialized", block.isInitialized(),
            "loaded", block.isLoaded(),
            "overlay", block.isOverlay(),
            "derived_relative_path", relativePath,
            "sha256", digest);
    }

    private Map<String, String> parseArguments(String[] values) {
        Map<String, String> result = new LinkedHashMap<>();
        for (int index = 0; index < values.length; ++index) {
            String value = values[index];
            if (!value.startsWith("--")) {
                throw new IllegalArgumentException(
                    "Arguments must start with --; received " + value);
            }
            int separator = value.indexOf('=');
            String name;
            String argumentValue;
            if (separator >= 3) {
                name = value.substring(2, separator);
                argumentValue = value.substring(separator + 1);
            }
            else {
                name = value.substring(2);
                if (index + 1 >= values.length || values[index + 1].startsWith("--")) {
                    throw new IllegalArgumentException("Missing value for --" + name);
                }
                argumentValue = values[++index];
            }
            String previous = result.put(name, argumentValue);
            if (previous != null) {
                throw new IllegalArgumentException("Duplicate argument " + value);
            }
        }
        return result;
    }

    private Path requiredDirectory(Map<String, String> arguments, String name) {
        String value = arguments.get(name);
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException("Missing --" + name + "=<path>");
        }
        return Paths.get(value).toAbsolutePath().normalize();
    }

    private long parseUnsignedDecimal(String value) {
        if (value == null || value.isBlank()) {
            return 0;
        }
        return Long.parseUnsignedLong(value);
    }

    private Long parseOptionalUnsignedDecimal(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        return Long.parseUnsignedLong(value);
    }

    private String emptyToNull(String value) {
        return value == null || value.isBlank() ? null : value;
    }

    private String decodeBase64(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        return new String(Base64.getDecoder().decode(value), StandardCharsets.UTF_8);
    }

    private long unsignedOffset(Address address) {
        return address == null ? 0 : address.getUnsignedOffset();
    }

    private long determineImageBase(List<MemoryBlock> blocks) {
        long programBase = unsignedOffset(currentProgram.getImageBase());
        if (programBase != 0) {
            return programBase;
        }
        for (MemoryBlock block : blocks) {
            if (block.isLoaded() && !block.isOverlay()) {
                return unsignedOffset(block.getStart()) & ~0xffffL;
            }
        }
        return 0;
    }

    private String sanitize(String value) {
        String sanitized = value.replaceAll("[^A-Za-z0-9_.-]", "_");
        return sanitized.isBlank() ? "block" : sanitized;
    }

    private String hex(long value) {
        return String.format(Locale.ROOT, "0x%08X", value);
    }

    private String hexDigest(byte[] value) {
        StringBuilder result = new StringBuilder(value.length * 2);
        for (byte item : value) {
            result.append(String.format(Locale.ROOT, "%02X", item & 0xff));
        }
        return result.toString();
    }

    private Map<String, Object> orderedMap(Object... values) {
        Map<String, Object> result = new LinkedHashMap<>();
        for (int index = 0; index < values.length; index += 2) {
            result.put((String)values[index], values[index + 1]);
        }
        return result;
    }

    private void writeJsonAtomically(Path output, Object value) throws IOException {
        Path temporary = output.resolveSibling(output.getFileName() + ".tmp");
        try (BufferedWriter writer = Files.newBufferedWriter(
                temporary, StandardCharsets.UTF_8)) {
            writeJson(writer, value, 0);
            writer.write('\n');
        }
        Files.move(temporary, output,
            java.nio.file.StandardCopyOption.REPLACE_EXISTING,
            java.nio.file.StandardCopyOption.ATOMIC_MOVE);
    }

    private void writeJson(BufferedWriter writer, Object value, int indentation)
            throws IOException {
        if (value == null) {
            writer.write("null");
        }
        else if (value instanceof String text) {
            writeJsonString(writer, text);
        }
        else if (value instanceof Number || value instanceof Boolean) {
            writer.write(value.toString());
        }
        else if (value instanceof Map<?, ?> map) {
            writer.write('{');
            boolean first = true;
            for (Map.Entry<?, ?> entry : map.entrySet()) {
                if (!first) {
                    writer.write(',');
                }
                first = false;
                newlineAndIndent(writer, indentation + 2);
                writeJsonString(writer, String.valueOf(entry.getKey()));
                writer.write(": ");
                writeJson(writer, entry.getValue(), indentation + 2);
            }
            if (!map.isEmpty()) {
                newlineAndIndent(writer, indentation);
            }
            writer.write('}');
        }
        else if (value instanceof List<?> list) {
            writer.write('[');
            for (int index = 0; index < list.size(); ++index) {
                if (index != 0) {
                    writer.write(',');
                }
                newlineAndIndent(writer, indentation + 2);
                writeJson(writer, list.get(index), indentation + 2);
            }
            if (!list.isEmpty()) {
                newlineAndIndent(writer, indentation);
            }
            writer.write(']');
        }
        else {
            throw new IllegalArgumentException("Unsupported JSON value " + value.getClass());
        }
    }

    private void newlineAndIndent(BufferedWriter writer, int indentation) throws IOException {
        writer.write('\n');
        writer.write(" ".repeat(indentation));
    }

    private void writeJsonString(BufferedWriter writer, String value) throws IOException {
        writer.write('"');
        for (int index = 0; index < value.length(); ++index) {
            char character = value.charAt(index);
            switch (character) {
                case '"' -> writer.write("\\\"");
                case '\\' -> writer.write("\\\\");
                case '\b' -> writer.write("\\b");
                case '\f' -> writer.write("\\f");
                case '\n' -> writer.write("\\n");
                case '\r' -> writer.write("\\r");
                case '\t' -> writer.write("\\t");
                default -> {
                    if (character < 0x20) {
                        writer.write(String.format(Locale.ROOT, "\\u%04X", (int)character));
                    }
                    else {
                        writer.write(character);
                    }
                }
            }
        }
        writer.write('"');
    }
}
