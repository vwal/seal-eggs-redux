"""Generate the Redux-only XOR patch from two verified local images.

Usage: python3 tools/make_delta.py <full-non-bright-seal-eggs.bin> <tested-v0.6.bin> <output.delta>
The distributable asset contains only a list of offsets, lengths and differences.
Equal bytes within a record are represented by zero. No input files are modified.
"""
import argparse
import hashlib
import struct
from pathlib import Path

BASE = "62842329515e79bb7c9c0cb3d9a4783c0cb6cd73d66ee6c4021668a0ddc0358b"
RELEASE = "0eec5c430a07f188f76a4efe243d1f160b7453ffdf0912da6f56614dbfb6de8f"


def image(path, expected):
    data = path.read_bytes()
    if len(data) != 589964 or hashlib.sha256(data).hexdigest() != expected:
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
    data = make_delta(image(args.base, BASE), image(args.redux, RELEASE))
    args.output.write_bytes(data)
    print(f"{args.output.name}   {len(data)} bytes   {hashlib.sha256(data).hexdigest()}")
