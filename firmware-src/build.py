#!/usr/bin/env python3
"""Rebuild and combine checked source patches for the audited Seal Eggs image.

Original firmware and input binaries are never opened for writing. The exact
input hash, every displaced instruction, all flash reservations, and the boot
RAM clear boundary are checked before an output image is created.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import subprocess
import sys
from build_utils import write_json

ROOT=Path(__file__).resolve().parent
BASE_SHA='62842329515e79bb7c9c0cb3d9a4783c0cb6cd73d66ee6c4021668a0ddc0358b'
RELEASE_SHA='0eec5c430a07f188f76a4efe243d1f160b7453ffdf0912da6f56614dbfb6de8f'
REGIONS={'doppler':(0x08058000,0x2000),'sunny':(0x0805a000,0x4000),
         'options':(0x0805e000,0x4000),'native-options':(0x08062000,0x4000),
         'diagnostics':(0x08066000,0x2000),'throw':(0x08068000,0x4000)}
BASE_ADDRESS=0x08000000
RAM_OLD_END=0x24070200
RAM_NEW_END=0x24072000

def sha(data):return hashlib.sha256(data).hexdigest()

def assemble(base, manifests):
    if sha(base)!=BASE_SHA:raise ValueError('Input is not the audited Seal Eggs non-bright firmware')
    if len(base)!=0x9008c:raise ValueError('Unexpected firmware length')
    out=bytearray(base)
    used={}
    records=[]
    seen=set()
    def insert(address, data, expected, owner):
        offset=address-BASE_ADDRESS
        if not 0<=offset<=len(base)-len(data):raise ValueError('Patch outside image: '+owner)
        if base[offset:offset+len(data)]!=expected:raise ValueError('Original bytes mismatch: '+owner)
        for i in range(offset,offset+len(data)):
            if i in used:raise ValueError('Overlapping patches: '+owner+' / '+used[i])
            used[i]=owner
        out[offset:offset+len(data)]=data
        records.append({'address':hex(address),'length':len(data),'owner':owner,
                        'before_sha256':sha(expected),'after_sha256':sha(data)})
    for manifest_path in manifests:
        m=json.loads(Path(manifest_path).read_text())
        name=m['name']
        if name in seen or name not in REGIONS:raise ValueError('Unexpected or duplicate component '+name)
        seen.add(name)
        start,capacity=REGIONS[name]
        if int(m['flash_start'],0)!=start:raise ValueError('Component at wrong flash origin: '+name)
        raw_path=Path(m['flash_file'])
        if not raw_path.is_absolute():raw_path=Path(manifest_path).parent/raw_path
        blob=raw_path.read_bytes()
        if not 0<len(blob)<=capacity:raise ValueError('Code reservation exceeded: '+name)
        offset=start-BASE_ADDRESS
        if any(base[offset:offset+capacity]):raise ValueError('Flash reservation is not empty: '+name)
        insert(start,blob,bytes(len(blob)),name+' code')
        for p in m['patches']:
            old=bytes.fromhex(p['expected']);new=bytes.fromhex(p['bytes'])
            if len(old)!=len(new):raise ValueError('Hook changes instruction span: '+name)
            insert(int(p['address'],0),new,old,name+': '+p['reason'])
    if seen!=set(REGIONS):raise ValueError('Missing component: '+str(set(REGIONS)-seen))
    insert(0x0802be9c,struct.pack('<I',RAM_NEW_END),struct.pack('<I',RAM_OLD_END),
           'Zero newly reserved option/state RAM at boot')
    if out[:0x400]!=base[:0x400]:raise ValueError('Interrupt vector table changed')
    if out[0x8bec4:]!=base[0x8bec4:]:raise ValueError('Native data initializer or image trailer changed')
    return bytes(out),records

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--manifests',type=Path,nargs=6,help='Combine already-built components')
    a=p.parse_args()
    base=a.base.resolve().read_bytes()
    if sha(base)!=BASE_SHA:raise SystemExit('Refusing unsupported input firmware hash')
    output=a.output.resolve()
    if output==a.base.resolve() or a.base.resolve().is_relative_to(output):
        raise SystemExit('Output must be separate from the source firmware')
    output.mkdir(parents=True,exist_ok=True)
    if a.manifests:
        manifests=a.manifests
    else:
        commands=[
          [sys.executable,str(ROOT/'doppler/build_hooks.py'),'--base',str(a.base.resolve()),'--out',str(output/'doppler')],
          [sys.executable,str(ROOT/'sunny/build.py'),'--base',str(a.base.resolve()),'--output',str(output/'sunny')],
          [sys.executable,str(ROOT/'options/build.py'),'--base',str(a.base.resolve()),'--output',str(output/'options')],
          [sys.executable,str(ROOT/'native/build_component.py'),'--base',str(a.base.resolve()),'--output',str(output/'native')],
          [sys.executable,str(ROOT/'diagnostics/build.py'),'--base',str(a.base.resolve()),'--output',str(output/'diagnostics')],
          [sys.executable,str(ROOT/'throw/build.py'),'--base',str(a.base.resolve()),'--output',str(output/'throw')],
        ]
        for command in commands:
            completed=subprocess.run(command,text=True,capture_output=True)
            if completed.returncode:
                sys.stderr.write(completed.stdout+completed.stderr)
                raise SystemExit(completed.returncode)
        manifests=[output/x/'manifest.json' for x in ['doppler','sunny','options','native','diagnostics','throw']]
    image,records=assemble(base,manifests)
    if sha(image) != RELEASE_SHA:
        raise SystemExit('Built bytes differ from release 1.3.5.0+c; check the documented compiler and sources')
    destination=output/'Sealegs.1.3.5.0+c.bin'
    destination.write_bytes(image)
    toolchain=subprocess.check_output(['arm-none-eabi-gcc','--version'],text=True).splitlines()[0]
    report={'release':'Seal Eggs Redux','version':'1.3.5.0+c', 'development_version':'0.6',
            'input_sha256':sha(base),'output_sha256':sha(image),'size':len(image),
            'toolchain':toolchain,'ram_reserved':['0x24070400',hex(RAM_NEW_END)],
            'patches':records}
    write_json(output/'build-report.json',report)
    print(json.dumps({'firmware':str(destination),'sha256':sha(image),'bytes':len(image),
                      'patch_regions':len(records)},indent=2))

if __name__=='__main__':main()
