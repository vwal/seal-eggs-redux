#!/usr/bin/env python3
"""Build the Throw component only; validate every replaced instruction."""
from pathlib import Path
import argparse,json,subprocess,struct,hashlib
HERE=Path(__file__).resolve().parent

def branch(pc,target,link=False):
 d=(target&~1)-(pc+4)
 if d%2 or not -(1<<24)<=d<(1<<24):raise ValueError('Thumb branch out of range')
 v=d&0x1ffffff;s=(v>>24)&1;i1=(v>>23)&1;i2=(v>>22)&1
 return struct.pack('<HH',0xf000|(s<<10)|((v>>12)&0x3ff),
                    (0xd000 if link else 0x9000)|((1^i1^s)<<13)|((1^i2^s)<<11)|((v>>1)&0x7ff))
def build(base,output,include=None):
 output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
 include=Path(include).resolve() if include else HERE.parent/'include'
 flags=['-mcpu=cortex-m7','-mthumb','-mfpu=fpv5-sp-d16','-mfloat-abi=hard',
        '-O2','-ffreestanding','-fno-builtin','-fno-unwind-tables',
        '-fno-asynchronous-unwind-tables','-ffunction-sections','-fdata-sections',
        '-Wall','-Wextra','-Werror','-I',str(include)]
 ld=output/'throw.ld'
 ld.write_text('ENTRY(throw_time_hook)\nSECTIONS { . = 0x08068000; .text : { *(.text.throw_hooks) *(.text*) *(.rodata*) } /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.ARM.exidx*) *(.ARM.extab*) } }\nASSERT(SIZEOF(.text)<=0x4000,"throw flash exceeded")\n')
 objects=[]
 for name in ['throw_hooks.S','throw_control.c','throw_audio.c']:
  obj=output/(Path(name).stem+'.o');objects.append(str(obj))
  subprocess.run(['arm-none-eabi-gcc',*flags,'-c',str(HERE/name),'-o',str(obj)],check=True)
 elf=output/'throw.elf';blob=output/'throw.bin'
 subprocess.run(['arm-none-eabi-gcc',*flags,'-nostdlib','-Wl,-T,'+str(ld),
                 '-Wl,-Map,'+str(output/'throw.map'),*objects,'-o',str(elf)],check=True)
 subprocess.run(['arm-none-eabi-objcopy','-O','binary',str(elf),str(blob)],check=True)
 syms={}
 for line in subprocess.check_output(['arm-none-eabi-nm','-n',str(elf)],text=True).splitlines():
  words=line.split()
  if len(words)==3:syms[words[2]]=int(words[0],16)
 data=Path(base).read_bytes();patches=[]
 for addr,expected,name,link in [(0x0801c448,'eef73af8','throw_time_hook',True),
                                 (0x0801b6e8,'d5f80862','throw_late_hook',False)]:
  off=addr-0x08000000
  if data[off:off+4].hex()!=expected:raise ValueError(f'hook mismatch at{addr:08x}')
  patches.append({'address':hex(addr),'expected':expected,'bytes':branch(addr,syms[name],link).hex(),'reason':name})
 manifest={'name':'throw','flash_start':'0x08068000','flash_file':str(blob),'size':blob.stat().st_size,
           'source_base_sha256':hashlib.sha256(data).hexdigest(),'symbols':{k:hex(v)for k,v in syms.items()},'patches':patches}
 (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 (output/'symbols.json').write_text(json.dumps(syms,indent=2)+'\n')
 (output/'throw.asm').write_text(subprocess.check_output(['arm-none-eabi-objdump','-d',str(elf)],text=True))
 print(json.dumps({'name':'throw','size':manifest['size'],'manifest':str(output/'manifest.json')}))
 return manifest
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True)
 p.add_argument('--out','--output',dest='out',type=Path,required=True);p.add_argument('--include',type=Path)
 a=p.parse_args();build(a.base,a.out,a.include)
