"""Append one bounded copy delta to a private XEXP copy; never execute the result.

Requires cryptography. Source/header/image snapshots stay private. The original
block chain is verified before rewriting its links and SHA-1 digests. This is a
loader test fixture, not a signed/distributable Xbox title update.
"""
import argparse
import hashlib
import struct
from pathlib import Path

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def u32(data, offset):
    return struct.unpack_from(">I", data, offset)[0]


def aes_decrypt(key, data):
    decryptor = Cipher(algorithms.AES(key), modes.CBC(bytes(16))).decryptor()
    return decryptor.update(data) + decryptor.finalize()


def make_fixture(source, headers, image, destination, old_offset, new_offset):
    if destination.exists() or source.resolve() == destination.resolve():
        raise ValueError("Destination must be a new private fixture file")
    patch = source.read_bytes()
    loaded_header = headers.read_bytes()
    loaded_image = image.read_bytes()
    assert patch[:4] == loaded_header[:4] == b"XEX2"
    assert 0 <= old_offset <= len(loaded_image) - 4
    assert 0 <= new_offset <= len(loaded_image) - 4
    assert loaded_image[old_offset:old_offset + 4] != loaded_image[new_offset:new_offset + 4]
    options = dict(struct.unpack_from(">II", patch, 24 + i * 8)
                   for i in range(u32(patch, 20)))
    fmt = options[0x3FF]
    encryption, compression = struct.unpack_from(">HH", patch, fmt + 4)
    assert encryption == 1 and compression == 3
    retail_key = bytes.fromhex("20B185A59D28FDC340583FBB0896BF91")
    loaded_key_at = u32(loaded_header, 16) + 0x150
    base_key = aes_decrypt(retail_key, loaded_header[loaded_key_at:loaded_key_at + 16])
    patch_key_at = u32(patch, 16) + 0x150
    patch_key = aes_decrypt(base_key, patch[patch_key_at:patch_key_at + 16])
    data_offset = u32(patch, 8)
    plaintext = aes_decrypt(patch_key, patch[data_offset:])
    size = u32(patch, fmt + 12)
    digest = patch[fmt + 16:fmt + 36]
    blocks = []
    cursor = 0
    while size:
        assert 24 <= size <= len(plaintext) - cursor
        block = plaintext[cursor:cursor + size]
        assert hashlib.sha1(block).digest() == digest
        blocks.append(block[24:])
        cursor += size
        size, digest = u32(block, 0), block[4:24]
    # compressed_len=1 means memmove, with no compressed payload (lzx.cpp).
    blocks.append(struct.pack(">IIHH", old_offset, new_offset, 4, 1))
    next_info = bytes(24)
    rewritten = []
    for payload in reversed(blocks):
        block = next_info + payload
        rewritten.append(block)
        next_info = struct.pack(">I", len(block)) + hashlib.sha1(block).digest()
    header = bytearray(patch[:data_offset])
    struct.pack_into(">H", header, fmt + 4, 0)  # supported unencrypted patch body
    header[fmt + 12:fmt + 36] = next_info
    destination.write_bytes(header + b"".join(reversed(rewritten)))
    return {"original_xexp_sha256": hashlib.sha256(patch).hexdigest().upper(),
            "fixture_xexp_sha256": hashlib.sha256(destination.read_bytes()).hexdigest().upper(),
            "copy_source_offset": hex(old_offset), "copy_target_offset": hex(new_offset),
            "original_word": loaded_image[new_offset:new_offset + 4].hex(),
            "replacement_word": loaded_image[old_offset:old_offset + 4].hex()}


if __name__ == "__main__":
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "headers", "image", "destination"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--old-offset", type=lambda x: int(x, 0), required=True)
    parser.add_argument("--new-offset", type=lambda x: int(x, 0), required=True)
    print(json.dumps(make_fixture(**vars(parser.parse_args())), indent=2))
