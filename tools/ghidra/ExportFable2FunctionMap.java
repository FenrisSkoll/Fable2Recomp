// Export a deterministic, byte-free Fable II function map from the current Ghidra program.
// @category Fable2
// @runtime Java

import java.io.BufferedWriter;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.NavigableMap;
import java.util.TreeMap;

import ghidra.app.script.GhidraScript;
import ghidra.framework.Application;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressRange;
import ghidra.program.model.address.AddressRangeIterator;
import ghidra.program.model.address.AddressSetView;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryAccessException;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.symbol.RefType;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.ReferenceManager;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;
import ghidra.program.model.symbol.SymbolTable;
import ghidra.program.model.symbol.SymbolType;
import ghidra.util.exception.CancelledException;

public class ExportFable2FunctionMap extends GhidraScript {
    private static final String SCHEMA_NAME = "fable2-ghidra-function-map";
    private static final long SCHEMA_VERSION = 1;
    private static final String EXPORTER_VERSION = "1.1.0";
    private static final String FINGERPRINT_ALGORITHM =
        "fable2-executable-memory-sha256-v1";
    private static final byte[] FINGERPRINT_MAGIC =
        "FABLE2_EXECUTABLE_MEMORY_V1\0".getBytes(StandardCharsets.US_ASCII);
    private static final int HASH_BUFFER_SIZE = 1024 * 1024;

    private record CanonicalSpan(
            long start,
            long end,
            int permissions,
            List<MemoryBlock> blocks) {
    }

    private record FunctionRecord(
            Function function,
            long entry,
            long extentStart,
            long extentEnd) {
    }

    private record ImageBaseEvidence(long value, String source) {
    }

    @Override
    protected void run() throws Exception {
        if (currentProgram == null) {
            throw new IllegalStateException(
                "No program is open. Use -process for an existing project or -import for a raw XEX.");
        }

        Map<String, String> arguments = parseArguments(getScriptArgs());
        Path outputPath = requiredOutputPath(arguments);
        validateProgram(arguments);

        Memory memory = currentProgram.getMemory();
        List<MemoryBlock> blocks = new ArrayList<>(Arrays.asList(memory.getBlocks()));
        blocks.sort(Comparator
            .comparingLong((MemoryBlock block) -> unsignedOffset(block.getStart()))
            .thenComparing(MemoryBlock::getName));

        List<Map<String, Object>> blockMaps = new ArrayList<>();
        for (MemoryBlock block : blocks) {
            blockMaps.add(exportMemoryBlock(block));
        }

        ImageBaseEvidence imageBase = determineImageBase(blocks, arguments);

        Map<String, Object> fingerprint = computeExecutableFingerprint(blocks);
        Map<Long, List<String>> pdataRecords = collectPdataRecords(blocks);
        List<FunctionRecord> functions = collectFunctions();
        Map<Long, List<Long>> overlaps = new HashMap<>();
        List<Map<String, Object>> overlapMaps = collectOverlaps(functions, overlaps);
        NavigableMap<Long, FunctionRecord> entries = new TreeMap<>();
        for (FunctionRecord function : functions) {
            entries.put(function.entry(), function);
        }

        List<Map<String, Object>> functionMaps = new ArrayList<>();
        monitor.initialize(functions.size(), "Exporting function evidence");
        for (FunctionRecord function : functions) {
            monitor.checkCancelled();
            functionMaps.add(exportFunction(function, pdataRecords, overlaps, entries));
            monitor.incrementProgress(1);
        }

        Map<String, Object> root = new LinkedHashMap<>();
        root.put("schema", orderedMap(
            "name", SCHEMA_NAME,
            "version", SCHEMA_VERSION));
        root.put("exporter", orderedMap(
            "name", "ExportFable2FunctionMap.java",
            "version", EXPORTER_VERSION,
            "commit", arguments.getOrDefault("exporter-commit", "unknown")));
        root.put("source_artifact", orderedMap(
            "id", arguments.getOrDefault("source-artifact", "local-ghidra-program"),
            "kind", arguments.getOrDefault("source-kind", "ghidra_project"),
            "url", emptyToNull(arguments.get("source-url")),
            "commit_or_release", emptyToNull(arguments.get("source-version")),
            "claimed_edition", emptyToNull(arguments.get("claimed-edition")),
            "claimed_region", emptyToNull(arguments.get("claimed-region")),
            "claimed_title_update", emptyToNull(arguments.get("claimed-title-update")),
            "project_path", currentProgram.getDomainFile().getPathname(),
            "program_name", currentProgram.getName(),
            "original_input_sha256", knownHash(arguments, "base-xex-sha256",
                currentProgram.getExecutableSHA256()),
            "title_update_sha256", knownHash(arguments, "title-update-sha256", null),
            "patched_image_sha256", knownHash(arguments, "patched-image-sha256", null)));
        root.put("toolchain", orderedMap(
            "ghidra_version", Application.getApplicationVersion(),
            "xexloader_version", arguments.getOrDefault("xexloader-version", "unknown"),
            "loader_name", arguments.getOrDefault("loader-name", currentProgram.getExecutableFormat()),
            "language_id", currentProgram.getLanguageID().getIdAsString(),
            "processor", currentProgram.getLanguage().getProcessor().toString(),
            "compiler_spec", currentProgram.getCompilerSpec()
                .getCompilerSpecID().getIdAsString()));
        root.put("program", orderedMap(
            "image_base", hex(imageBase.value()),
            "image_base_source", imageBase.source(),
            "executable_format", currentProgram.getExecutableFormat(),
            "executable_sha256", emptyToNull(currentProgram.getExecutableSHA256()),
            "memory_block_count", (long) blockMaps.size(),
            "function_count", (long) functionMaps.size()));
        root.put("identity_evidence", orderedMap(
            "base_xex_sha256", knownHash(arguments, "base-xex-sha256",
                currentProgram.getExecutableSHA256()),
            "title_update_sha256", knownHash(arguments, "title-update-sha256", null),
            "patched_image_sha256", knownHash(arguments, "patched-image-sha256", null),
            "executable_memory_fingerprint_algorithm", FINGERPRINT_ALGORITHM,
            "executable_memory_fingerprint", fingerprint.get("sha256"),
            "executable_memory_fingerprint_status", fingerprint.get("status"),
            "image_base", hex(imageBase.value()),
            "image_base_source", imageBase.source(),
            "memory_blocks", blockMaps));
        root.put("pdata_functions", exportPdataFunctions(pdataRecords));
        root.put("functions", functionMaps);
        root.put("overlaps", overlapMaps);

        Path parent = outputPath.getParent();
        if (parent != null) {
            Files.createDirectories(parent);
        }
        Path temporary = outputPath.resolveSibling(outputPath.getFileName() + ".tmp");
        try (BufferedWriter writer = Files.newBufferedWriter(
                temporary, StandardCharsets.UTF_8)) {
            writeJson(writer, root, 0);
            writer.write('\n');
        }
        Files.move(temporary, outputPath,
            java.nio.file.StandardCopyOption.REPLACE_EXISTING,
            java.nio.file.StandardCopyOption.ATOMIC_MOVE);
        println("Exported " + functionMaps.size() + " functions to " + outputPath);
        println("Executable-memory fingerprint: " + fingerprint.get("status") + " " +
            fingerprint.get("sha256"));
    }

    private Map<String, String> parseArguments(String[] scriptArguments) {
        Map<String, String> values = new HashMap<>();
        for (int index = 0; index < scriptArguments.length; ++index) {
            String argument = scriptArguments[index];
            int separator = argument.indexOf('=');
            if (!argument.startsWith("--")) {
                throw new IllegalArgumentException(
                    "Exporter arguments must start with --; received '" + argument + "'");
            }
            String name;
            String value;
            if (separator >= 3) {
                name = argument.substring(2, separator);
                value = argument.substring(separator + 1);
            }
            else {
                name = argument.substring(2);
                value = "";
                if (index + 1 < scriptArguments.length &&
                        !scriptArguments[index + 1].startsWith("--")) {
                    value = scriptArguments[++index];
                }
            }
            if (values.put(name, value) != null) {
                throw new IllegalArgumentException("Duplicate exporter argument --" + name);
            }
        }
        return values;
    }

    private Path requiredOutputPath(Map<String, String> arguments) {
        String output = arguments.get("output");
        if (output == null || output.isBlank()) {
            throw new IllegalArgumentException("Missing required exporter argument --output=<path>");
        }
        return Paths.get(output).toAbsolutePath().normalize();
    }

    private void validateProgram(Map<String, String> arguments) {
        String expectedLanguage = arguments.getOrDefault(
            "expected-language", "PowerPC:BE:64:A2ALT-32addr");
        String actualLanguage = currentProgram.getLanguageID().getIdAsString();
        if (!actualLanguage.equals(expectedLanguage)) {
            throw new IllegalStateException(
                "Wrong Ghidra language: expected " + expectedLanguage + ", found " + actualLanguage);
        }
        if (!currentProgram.getLanguage().isBigEndian()) {
            throw new IllegalStateException("Fable II export requires a big-endian Ghidra program");
        }
    }

    private ImageBaseEvidence determineImageBase(
            List<MemoryBlock> blocks, Map<String, String> arguments) {
        String supplied = arguments.get("image-base");
        if (supplied != null && !supplied.isBlank()) {
            try {
                String digits = supplied.startsWith("0x") || supplied.startsWith("0X")
                    ? supplied.substring(2) : supplied;
                return new ImageBaseEvidence(
                    Long.parseUnsignedLong(digits, 16), "export_argument");
            }
            catch (NumberFormatException error) {
                throw new IllegalArgumentException(
                    "--image-base must be an unsigned hexadecimal address", error);
            }
        }
        long programBase = unsignedOffset(currentProgram.getImageBase());
        if (programBase != 0) {
            return new ImageBaseEvidence(programBase, "ghidra_program_image_base");
        }
        for (MemoryBlock block : blocks) {
            if (block.isLoaded() && !block.isOverlay()) {
                long inferred = unsignedOffset(block.getStart()) & ~0xffffL;
                return new ImageBaseEvidence(
                    inferred, "inferred_64k_aligned_first_loaded_block");
            }
        }
        return new ImageBaseEvidence(0, "ghidra_program_image_base");
    }

    private List<FunctionRecord> collectFunctions() {
        List<FunctionRecord> result = new ArrayList<>();
        FunctionIterator iterator = currentProgram.getFunctionManager().getFunctions(true);
        while (iterator.hasNext()) {
            Function function = iterator.next();
            AddressSetView body = function.getBody();
            long entry = unsignedOffset(function.getEntryPoint());
            long extentStart = body.isEmpty() ? entry : unsignedOffset(body.getMinAddress());
            long extentEnd = body.isEmpty() ? entry : exclusiveEnd(body.getMaxAddress());
            result.add(new FunctionRecord(function, entry, extentStart, extentEnd));
        }
        result.sort(Comparator
            .comparingLong(FunctionRecord::entry)
            .thenComparing(record -> record.function().getName()));
        return result;
    }

    private Map<String, Object> exportMemoryBlock(MemoryBlock block) throws Exception {
        String hash = null;
        String hashStatus = "not_initialized";
        if (block.isInitialized() && block.isLoaded() && !block.isOverlay()) {
            hash = hashBlock(block);
            hashStatus = "complete";
        }
        return orderedMap(
            "name", block.getName(),
            "range", rangeMap(unsignedOffset(block.getStart()), exclusiveEnd(block.getEnd())),
            "permissions", orderedMap(
                "read", block.isRead(),
                "write", block.isWrite(),
                "execute", block.isExecute()),
            "initialized", block.isInitialized(),
            "loaded", block.isLoaded(),
            "overlay", block.isOverlay(),
            "mapped", block.isMapped(),
            "artificial", block.isArtificial(),
            "volatile", block.isVolatile(),
            "source_name", block.getSourceName(),
            "sha256", hash,
            "hash_status", hashStatus);
    }

    private Map<String, Object> computeExecutableFingerprint(List<MemoryBlock> allBlocks)
            throws Exception {
        List<MemoryBlock> executable = new ArrayList<>();
        for (MemoryBlock block : allBlocks) {
            if (block.isExecute() && block.isLoaded() && !block.isOverlay() && block.getSize() != 0) {
                if (!block.isInitialized()) {
                    return orderedMap(
                        "status", "incomplete_uninitialized_executable_block:" + block.getName(),
                        "sha256", null);
                }
                executable.add(block);
            }
        }
        executable.sort(Comparator.comparingLong(block -> unsignedOffset(block.getStart())));

        List<CanonicalSpan> spans = new ArrayList<>();
        for (MemoryBlock block : executable) {
            long start = unsignedOffset(block.getStart());
            long end = exclusiveEnd(block.getEnd());
            int permissions = permissionBits(block);
            if (!spans.isEmpty() && start < spans.get(spans.size() - 1).end()) {
                return orderedMap(
                    "status", "invalid_overlapping_executable_blocks:" + block.getName(),
                    "sha256", null);
            }
            if (!spans.isEmpty()) {
                CanonicalSpan previous = spans.get(spans.size() - 1);
                if (start == previous.end() && permissions == previous.permissions()) {
                    List<MemoryBlock> merged = new ArrayList<>(previous.blocks());
                    merged.add(block);
                    spans.set(spans.size() - 1,
                        new CanonicalSpan(previous.start(), end, permissions, merged));
                    continue;
                }
            }
            spans.add(new CanonicalSpan(start, end, permissions, List.of(block)));
        }

        MessageDigest digest = sha256();
        digest.update(FINGERPRINT_MAGIC);
        updateBe32(digest, spans.size());
        for (CanonicalSpan span : spans) {
            updateBe64(digest, span.start());
            updateBe64(digest, span.end() - span.start());
            digest.update((byte) span.permissions());
            for (MemoryBlock block : span.blocks()) {
                updateDigestFromBlock(digest, block);
            }
        }
        return orderedMap("status", "complete", "sha256", hexDigest(digest.digest()));
    }

    private Map<Long, List<String>> collectPdataRecords(List<MemoryBlock> blocks)
            throws MemoryAccessException, CancelledException {
        Map<Long, List<String>> result = new HashMap<>();
        Memory memory = currentProgram.getMemory();
        for (MemoryBlock block : blocks) {
            if (!block.getName().equalsIgnoreCase(".pdata") || !block.isInitialized()) {
                continue;
            }
            long recordCount = block.getSize() / 8;
            for (long index = 0; index < recordCount; ++index) {
                monitor.checkCancelled();
                Address recordAddress = block.getStart().add(index * 8);
                long functionAddress = Integer.toUnsignedLong(memory.getInt(recordAddress, true));
                result.computeIfAbsent(functionAddress, ignored -> new ArrayList<>())
                    .add(hex(recordAddress));
            }
        }
        for (List<String> records : result.values()) {
            records.sort(String::compareTo);
        }
        return result;
    }

    private List<Map<String, Object>> exportPdataFunctions(
            Map<Long, List<String>> pdataRecords) {
        List<Long> entries = new ArrayList<>(pdataRecords.keySet());
        entries.sort(Long::compareUnsigned);
        List<Map<String, Object>> result = new ArrayList<>();
        for (Long entry : entries) {
            result.add(orderedMap(
                "entry", hex(entry),
                "record_addresses", new ArrayList<>(pdataRecords.get(entry))));
        }
        return result;
    }

    private List<Map<String, Object>> collectOverlaps(
            List<FunctionRecord> functions,
            Map<Long, List<Long>> overlapEntries) {
        List<FunctionRecord> byExtent = new ArrayList<>(functions);
        byExtent.sort(Comparator
            .comparingLong(FunctionRecord::extentStart)
            .thenComparingLong(FunctionRecord::extentEnd)
            .thenComparingLong(FunctionRecord::entry));
        List<FunctionRecord> active = new ArrayList<>();
        List<Map<String, Object>> result = new ArrayList<>();
        for (FunctionRecord current : byExtent) {
            active.removeIf(item -> item.extentEnd() <= current.extentStart());
            for (FunctionRecord other : active) {
                AddressSetView intersection =
                    current.function().getBody().intersect(other.function().getBody());
                if (intersection.isEmpty()) {
                    continue;
                }
                long firstEntry = Math.min(current.entry(), other.entry());
                long secondEntry = Math.max(current.entry(), other.entry());
                overlapEntries.computeIfAbsent(firstEntry, ignored -> new ArrayList<>())
                    .add(secondEntry);
                overlapEntries.computeIfAbsent(secondEntry, ignored -> new ArrayList<>())
                    .add(firstEntry);
                result.add(orderedMap(
                    "entries", List.of(hex(firstEntry), hex(secondEntry)),
                    "body_ranges", addressRanges(intersection)));
            }
            active.add(current);
        }
        result.sort(Comparator.comparing(item -> ((List<String>) item.get("entries")).get(0) +
            ((List<String>) item.get("entries")).get(1)));
        for (List<Long> values : overlapEntries.values()) {
            values.sort(Long::compareUnsigned);
        }
        return result;
    }

    private Map<String, Object> exportFunction(
            FunctionRecord record,
            Map<Long, List<String>> pdataRecords,
            Map<Long, List<Long>> overlaps,
            NavigableMap<Long, FunctionRecord> entries) {
        Function function = record.function();
        AddressSetView body = function.getBody();
        List<Map<String, Object>> bodyRanges = addressRanges(body);
        long bodySize = body.getNumAddresses();

        SymbolTable symbols = currentProgram.getSymbolTable();
        Symbol primary = function.getSymbol();
        List<Map<String, Object>> aliases = new ArrayList<>();
        for (Symbol symbol : symbols.getSymbols(function.getEntryPoint())) {
            if (symbol.getSymbolType() == SymbolType.FUNCTION ||
                    symbol.getSymbolType() == SymbolType.LABEL) {
                aliases.add(symbolMap(symbol));
            }
        }
        aliases.sort(Comparator
            .comparing((Map<String, Object> value) -> !(Boolean) value.get("primary"))
            .thenComparing(value -> (String) value.get("name"))
            .thenComparing(value -> (String) value.get("source_type")));

        Map<String, Object> thunk = null;
        if (function.isThunk()) {
            Function direct = function.getThunkedFunction(false);
            Function terminal = function.getThunkedFunction(true);
            thunk = orderedMap(
                "is_thunk", true,
                "direct_target", direct == null ? null : hex(direct.getEntryPoint()),
                "terminal_target", terminal == null ? null : hex(terminal.getEntryPoint()),
                "target_name", terminal == null ? null : terminal.getName());
        }

        List<String> otherEntries = new ArrayList<>();
        if (!body.isEmpty()) {
            NavigableMap<Long, FunctionRecord> candidates = entries.subMap(
                record.extentStart(), true, record.extentEnd(), false);
            for (FunctionRecord candidate : candidates.values()) {
                if (candidate.entry() != record.entry() &&
                        body.contains(candidate.function().getEntryPoint())) {
                    otherEntries.add(hex(candidate.entry()));
                }
            }
        }

        List<String> overlapList = new ArrayList<>();
        for (Long entry : overlaps.getOrDefault(record.entry(), List.of())) {
            overlapList.add(hex(entry));
        }

        return orderedMap(
            "entry", hex(record.entry()),
            "body_ranges", bodyRanges,
            "body_size", hex(bodySize),
            "extent", rangeMap(record.extentStart(), record.extentEnd()),
            "contiguous_body", bodyRanges.size() <= 1,
            "primary_name", orderedMap(
                "name", function.getName(),
                "source_type", sourceName(primary.getSource())),
            "aliases", aliases,
            "external", function.isExternal(),
            "imported", function.isExternal(),
            "entrypoint", symbols.isExternalEntryPoint(function.getEntryPoint()),
            "no_return", function.hasNoReturn(),
            "calling_convention", emptyToNull(function.getCallingConventionName()),
            "signature_source_type", sourceName(function.getSignatureSource()),
            "thunk", thunk,
            "pdata_records", new ArrayList<>(pdataRecords.getOrDefault(record.entry(), List.of())),
            "inbound_references", inboundReferences(function.getEntryPoint()),
            "callable_internal_labels", callableInternalLabels(function),
            "other_function_entries_in_body", otherEntries,
            "overlapping_function_entries", overlapList);
    }

    private List<Map<String, Object>> inboundReferences(Address address) {
        List<Map<String, Object>> references = new ArrayList<>();
        ReferenceIterator iterator = currentProgram.getReferenceManager().getReferencesTo(address);
        while (iterator.hasNext()) {
            references.add(referenceMap(iterator.next()));
        }
        references.sort(referenceComparator());
        return references;
    }

    private List<Map<String, Object>> callableInternalLabels(Function function) {
        List<Map<String, Object>> labels = new ArrayList<>();
        SymbolIterator iterator = currentProgram.getSymbolTable().getSymbols(
            function.getBody(), SymbolType.LABEL, true);
        ReferenceManager references = currentProgram.getReferenceManager();
        while (iterator.hasNext()) {
            Symbol symbol = iterator.next();
            if (symbol.getAddress().equals(function.getEntryPoint())) {
                continue;
            }
            List<Map<String, Object>> inbound = new ArrayList<>();
            ReferenceIterator referenceIterator = references.getReferencesTo(symbol.getAddress());
            while (referenceIterator.hasNext()) {
                Reference reference = referenceIterator.next();
                RefType type = reference.getReferenceType();
                if (type.isCall() || type.isJump()) {
                    inbound.add(referenceMap(reference));
                }
            }
            if (!inbound.isEmpty()) {
                inbound.sort(referenceComparator());
                labels.add(orderedMap(
                    "address", hex(symbol.getAddress()),
                    "name", symbol.getName(true),
                    "source_type", sourceName(symbol.getSource()),
                    "inbound_code_references", inbound));
            }
        }
        labels.sort(Comparator
            .comparing((Map<String, Object> value) -> (String) value.get("address"))
            .thenComparing(value -> (String) value.get("name")));
        return labels;
    }

    private Map<String, Object> referenceMap(Reference reference) {
        RefType type = reference.getReferenceType();
        String category = type.isCall() || type.isJump() || type.isFlow() ? "code" : "data";
        return orderedMap(
            "from", hex(reference.getFromAddress()),
            "to", hex(reference.getToAddress()),
            "category", category,
            "type", type.getName(),
            "source_type", sourceName(reference.getSource()),
            "operand_index", (long) reference.getOperandIndex(),
            "primary", reference.isPrimary());
    }

    private Comparator<Map<String, Object>> referenceComparator() {
        return Comparator
            .comparing((Map<String, Object> value) -> (String) value.get("from"))
            .thenComparing(value -> (String) value.get("to"))
            .thenComparing(value -> (String) value.get("type"))
            .thenComparingLong(value -> (Long) value.get("operand_index"));
    }

    private Map<String, Object> symbolMap(Symbol symbol) {
        return orderedMap(
            "name", symbol.getName(true),
            "source_type", sourceName(symbol.getSource()),
            "symbol_type", symbol.getSymbolType().toString().toLowerCase(Locale.ROOT),
            "primary", symbol.isPrimary(),
            "external", symbol.isExternal());
    }

    private List<Map<String, Object>> addressRanges(AddressSetView body) {
        List<Map<String, Object>> ranges = new ArrayList<>();
        AddressRangeIterator iterator = body.getAddressRanges(true);
        while (iterator.hasNext()) {
            AddressRange range = iterator.next();
            ranges.add(rangeMap(unsignedOffset(range.getMinAddress()),
                exclusiveEnd(range.getMaxAddress())));
        }
        return ranges;
    }

    private Map<String, Object> rangeMap(long start, long end) {
        return orderedMap(
            "start", hex(start),
            "end", hex(end),
            "size", hex(end - start));
    }

    private String hashBlock(MemoryBlock block) throws Exception {
        MessageDigest digest = sha256();
        updateDigestFromBlock(digest, block);
        return hexDigest(digest.digest());
    }

    private void updateDigestFromBlock(MessageDigest digest, MemoryBlock block)
            throws MemoryAccessException, CancelledException {
        byte[] buffer = new byte[HASH_BUFFER_SIZE];
        long consumed = 0;
        while (consumed < block.getSize()) {
            monitor.checkCancelled();
            int requested = (int) Math.min(buffer.length, block.getSize() - consumed);
            int read = block.getBytes(block.getStart().add(consumed), buffer, 0, requested);
            if (read != requested) {
                throw new MemoryAccessException(
                    "Short read from block " + block.getName() + " at +0x" +
                    Long.toHexString(consumed));
            }
            digest.update(buffer, 0, read);
            consumed += read;
        }
    }

    private MessageDigest sha256() {
        try {
            return MessageDigest.getInstance("SHA-256");
        }
        catch (NoSuchAlgorithmException error) {
            throw new IllegalStateException("JVM does not provide SHA-256", error);
        }
    }

    private void updateBe32(MessageDigest digest, long value) {
        digest.update((byte) (value >>> 24));
        digest.update((byte) (value >>> 16));
        digest.update((byte) (value >>> 8));
        digest.update((byte) value);
    }

    private void updateBe64(MessageDigest digest, long value) {
        digest.update((byte) (value >>> 56));
        digest.update((byte) (value >>> 48));
        digest.update((byte) (value >>> 40));
        digest.update((byte) (value >>> 32));
        digest.update((byte) (value >>> 24));
        digest.update((byte) (value >>> 16));
        digest.update((byte) (value >>> 8));
        digest.update((byte) value);
    }

    private int permissionBits(MemoryBlock block) {
        return (block.isRead() ? 1 : 0) |
            (block.isWrite() ? 2 : 0) |
            (block.isExecute() ? 4 : 0);
    }

    private long unsignedOffset(Address address) {
        BigInteger value = address.getOffsetAsBigInteger();
        if (value.signum() < 0 || value.bitLength() > 63) {
            throw new IllegalArgumentException("Address cannot be represented in map schema: " + address);
        }
        return value.longValueExact();
    }

    private long exclusiveEnd(Address inclusiveEnd) {
        return Math.addExact(unsignedOffset(inclusiveEnd), 1);
    }

    private String hex(Address address) {
        return hex(unsignedOffset(address));
    }

    private String hex(long value) {
        if (value >= 0 && value <= 0xffffffffL) {
            return String.format(Locale.ROOT, "0x%08X", value);
        }
        return String.format(Locale.ROOT, "0x%016X", value);
    }

    private String hexDigest(byte[] digest) {
        StringBuilder result = new StringBuilder(digest.length * 2);
        for (byte value : digest) {
            result.append(String.format(Locale.ROOT, "%02X", value & 0xff));
        }
        return result.toString();
    }

    private String sourceName(Object source) {
        return source == null ? "unknown" : source.toString().toLowerCase(Locale.ROOT);
    }

    private Object knownHash(Map<String, String> arguments, String key, String fallback) {
        String value = arguments.get(key);
        if (value == null || value.isBlank()) {
            value = fallback;
        }
        return emptyToNull(value == null ? null : value.toUpperCase(Locale.ROOT));
    }

    private Object emptyToNull(String value) {
        return value == null || value.isBlank() ? null : value;
    }

    private Map<String, Object> orderedMap(Object... values) {
        if ((values.length & 1) != 0) {
            throw new IllegalArgumentException("orderedMap requires key/value pairs");
        }
        Map<String, Object> result = new LinkedHashMap<>();
        for (int index = 0; index < values.length; index += 2) {
            result.put((String) values[index], values[index + 1]);
        }
        return result;
    }

    @SuppressWarnings("unchecked")
    private void writeJson(BufferedWriter writer, Object value, int indentation) throws IOException {
        if (value == null) {
            writer.write("null");
        }
        else if (value instanceof String text) {
            writeJsonString(writer, text);
        }
        else if (value instanceof Boolean || value instanceof Number) {
            writer.write(value.toString());
        }
        else if (value instanceof Map<?, ?> map) {
            writer.write('{');
            if (!map.isEmpty()) {
                boolean first = true;
                for (Map.Entry<String, Object> entry : ((Map<String, Object>) map).entrySet()) {
                    if (!first) {
                        writer.write(',');
                    }
                    newlineAndIndent(writer, indentation + 2);
                    writeJsonString(writer, entry.getKey());
                    writer.write(": ");
                    writeJson(writer, entry.getValue(), indentation + 2);
                    first = false;
                }
                newlineAndIndent(writer, indentation);
            }
            writer.write('}');
        }
        else if (value instanceof List<?> list) {
            writer.write('[');
            if (!list.isEmpty()) {
                for (int index = 0; index < list.size(); ++index) {
                    if (index != 0) {
                        writer.write(',');
                    }
                    newlineAndIndent(writer, indentation + 2);
                    writeJson(writer, list.get(index), indentation + 2);
                }
                newlineAndIndent(writer, indentation);
            }
            writer.write(']');
        }
        else {
            throw new IllegalArgumentException("Unsupported JSON value: " + value.getClass());
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
                        writer.write(String.format(Locale.ROOT, "\\u%04X", (int) character));
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
