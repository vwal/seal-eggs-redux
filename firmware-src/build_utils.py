"""Small checked ARM patch build helpers; no external assembler packages."""
from pathlib import Path
import json
import struct
import subprocess

FLASH_BASE = 0x08000000

def thumb_branch(source, target, link=False):
    target &= ~1
    displacement = target - (source + 4)
    if displacement & 1 or not -(1 << 24) <= displacement < (1 << 24):
        raise ValueError('Thumb branch outside signed 25-bit displacement')
    n = displacement & 0x1ffffff
    s = (n >> 24) & 1
    i1, i2 = (n >> 23) & 1, (n >> 22) & 1
    j1, j2 = (~(i1 ^ s)) & 1, (~(i2 ^ s)) & 1
    first = 0xf000 | (s << 10) | ((n >> 12) & 0x3ff)
    second = (0xd000 if link else 0x9000) | (j1 << 13) | (j2 << 11) | ((n >> 1) & 0x7ff)
    return struct.pack('<HH', first, second)

def symbols(elf):
    result = {}
    output = subprocess.check_output(['arm-none-eabi-nm', '-n', str(elf)], text=True)
    for line in output.splitlines():
        words = line.split()
        if len(words) == 3:
            result[words[2]] = int(words[0], 16)
    return result

def patch(base, address, data, reason):
    offset = address - FLASH_BASE
    if not 0 <= offset <= len(base) - len(data):
        raise ValueError('patch outside firmware image')
    return {'address': hex(address), 'expected': base[offset:offset+len(data)].hex(),
            'bytes': data.hex(), 'reason': reason}

def run(command, cwd):
    subprocess.run(command, cwd=cwd, check=True)

def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')
