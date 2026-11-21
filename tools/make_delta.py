"""Generate an XOR patch to the tested Redux release from a verified local source.

Usage: python3 tools/make_delta.py <stock-or-full-seal-eggs.bin> <Sealegs.1.3.5.0+c.bin> <output.delta>
The distributable asset contains only a list of offsets, lengths and differences.
Equal bytes within a record are represented by zero. No input files are modified.
"""
import argparse
import hashlib
import struct
from pathlib import Path

STOCK = "ca90eb8f0d7e491d548597fab696bca6d54f30b8bbda5b669c3a426508d8adcf"
SEAL_EGGS = "62842329515e79bb7c9c0cb3d9a4783c0cb6cd73d66ee6c4021668a0ddc0358b"
RELEASE = "0eec5c430a07f188f76a4efe243d1f160b7453ffdf0912da6f56614dbfb6de8f"


def image(path, *accepted_hashes):
    data = path.read_bytes()
    if len(data) != 589964 or hashlib.sha256(data).hexdigest() not in accepted_hashes:
        raise ValueError(f"{path} is not the expected input for this release")
    return data


def make_delta(original, release):
    differences = bytes(a ^ b for a, b in zip(original, release, strict=True))
    positions = [i for i, byte in enumerate(differences) if byte]
    result = bytearray(b"SRX1")
    start = last = positions[0]
    for pos in positions[1:]:
        if pos - last > 7 or pos - start > 65534:
            result.extend(struct.pack("<IH", start, last - start + 1))
            result.extend(differences[start:last + 1])
            start = pos
        last = pos
    result.extend(struct.pack("<IH", start, last - start + 1))
    result.extend(differences[start:last + 1])
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", type=Path)
    parser.add_argument("redux", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    data = make_delta(image(args.base, STOCK, SEAL_EGGS), image(args.redux, RELEASE))
    args.output.write_bytes(data)
    print(f"{args.output.name}   {len(data)} bytes   {hashlib.sha256(data).hexdigest()}")
