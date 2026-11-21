#!/usr/bin/env python3
from pathlib import Path
import argparse
import struct
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_utils import run, symbols, patch, thumb_branch, write_json

HERE = Path(__file__).resolve().parent

def build(base_path, output):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    base = Path(base_path).read_bytes()
    flags = ['-mcpu=cortex-m7', '-mthumb', '-mfpu=fpv5-sp-d16', '-mfloat-abi=hard',
             '-Os', '-ffreestanding', '-fno-builtin', '-fno-unwind-tables',
             '-fno-asynchronous-unwind-tables', '-ffunction-sections', '-fdata-sections',
             '-Wall', '-Wextra', '-Werror']
    for name in ['native.c', 'hooks.S']:
        run(['arm-none-eabi-gcc', *flags, '-c', str(HERE/name), '-o', str(output/(name+'.o'))], HERE)
    elf = output/'native.elf'
    run(['arm-none-eabi-gcc', *flags, '-nostdlib', '-Wl,-T,'+str(HERE/'link.ld'),
         '-Wl,-Map,'+str(output/'native.map'), '-o', str(elf),
         str(output/'hooks.S.o'), str(output/'native.c.o')], HERE)
    binary = output/'native.bin'
    run(['arm-none-eabi-objcopy', '-O', 'binary', str(elf), str(binary)], HERE)
    sym = symbols(elf)
    hooks = [
      (0x08018d80, 'tape_audio_hook', False),
      (0x0801296e, 'bbd_control_hook', True),
      (0x08018e42, 'pickup_left_slow', False),
      (0x08018e46, 'pickup_left_fast', False),
      (0x08019ff0, 'pickup_right_a', False),
      (0x0801a000, 'pickup_right_b', False),
      (0x0801a186, 'pickup_right_c', False),
      (0x0801a192, 'pickup_right_d', False),
      (0x080113d2, 'bbd_threshold_left', False),
      (0x080115b0, 'bbd_threshold_right', False),
      (0x080114f8, 'bbd_cap_left_a', False),
      (0x0801165c, 'bbd_cap_right_a', False),
      (0x08011886, 'bbd_cap_left_b', False),
      (0x08011892, 'bbd_cap_right_b', False),
    ]
    patches = [patch(base, a, thumb_branch(a, sym[n], bl), n) for a,n,bl in hooks]
    # Both shelf initializers retain the original firmware gains. Live options
    # use the native dirty/recompute path, independent of the input variant.
    for a,f in [(0x08011308,-6.1),(0x08011368,3.0)]:
        patches.append(patch(base,a,struct.pack('<f',f),'Stock Tape shelf initialization'))
    write_json(output/'symbols.json', sym)
    manifest = {'name':'native-options','flash_start':'0x08062000',
                'flash_file':str(binary),'patches':patches}
    write_json(output/'manifest.json',manifest)
    return manifest

if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--base', required=True)
    p.add_argument('--output', required=True)
    a=p.parse_args()
    build(a.base,a.output)
