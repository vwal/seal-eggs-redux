"""Build only Sunny hooks; never modifies the supplied base firmware."""
from pathlib import Path
import subprocess,struct,json,hashlib,argparse
SOURCE=Path(__file__).resolve().parent
from generate_cold_coefficients import render
assert (SOURCE/'cold_coefficients.h').read_text()==render(), 'Cold FIR table differs from reproducible generator'
parser=argparse.ArgumentParser()
parser.add_argument('--base',type=Path,required=True,help='Audited no-bright Seal Eggs image')
parser.add_argument('--output',type=Path,required=True,help='Component artifact directory')
args=parser.parse_args();ROOT=args.output.resolve();ROOT.mkdir(parents=True,exist_ok=True)
image=args.base.read_bytes()
assert hashlib.sha256(image).hexdigest()=='62842329515e79bb7c9c0cb3d9a4783c0cb6cd73d66ee6c4021668a0ddc0358b','Unexpected input firmware SHA-256'
subprocess.run(['arm-none-eabi-gcc','-mcpu=cortex-m7','-mthumb','-mfpu=fpv5-d16','-mfloat-abi=hard','-Os','-ffreestanding','-fno-builtin','-fno-unwind-tables','-fno-asynchronous-unwind-tables','-nostdlib','-Wl,--build-id=none','-Wl,-T,'+str(SOURCE/'sunny.ld'),str(SOURCE/'sunny.c'),str(SOURCE/'cold.c'),'-o',str(ROOT/'sunny.elf')],check=True)
subprocess.run(['arm-none-eabi-objcopy','-O','binary',str(ROOT/'sunny.elf'),str(ROOT/'sunny.bin')],check=True)
syms={}
for line in subprocess.check_output(['arm-none-eabi-nm',str(ROOT/'sunny.elf')],text=True).splitlines():
 x=line.split()
 if len(x)==3:syms[x[2]]=int(x[0],16)
def bl(src,dst):
 delta=dst-src-4
 assert delta%2==0 and -(1<<24)<=delta<(1<<24)
 v=delta&0x1ffffff;s=(v>>24)&1;i1=(v>>23)&1;i2=(v>>22)&1
 return struct.pack('<HH',0xf000|(s<<10)|((v>>12)&0x3ff),0xd000|((1^(i1^s))<<13)|((1^(i2^s))<<11)|((v>>1)&0x7ff))
patches=[]
for addr,sym,reason in [(0x0803b8e2,'sunny_configure','Select remembered Beads quality only after bounded engine-entry clear'),(0x0803f2ba,'sunny_process','Preserve grain timing through Sunny half-rate and Cold two-thirds-rate engines')]:
 patches.append({'address':hex(addr),'expected':image[addr-0x08000000:addr-0x08000000+4].hex(),'bytes':bl(addr,syms[sym]).hex(),'reason':reason})
blob=(ROOT/'sunny.bin').read_bytes();assert len(blob)<=0x4000
assert not any(image[0x5a000:0x5a000+len(blob)])
manifest={'name':'sunny','flash_start':'0x0805a000','flash_file':str(ROOT/'sunny.bin'),'patches':patches,'symbols':{k:hex(v) for k,v in syms.items() if k.startswith(('sunny_', 'cold_'))},'ram_status':{'active_quality':'0x24070800','valid':'0x24070801'},'base_sha256':hashlib.sha256(image).hexdigest()}
manifest['cold_state'] = {'start':'0x24071000', 'reserved_bytes':4096, 'used_bytes':struct.unpack_from('<I',blob,syms['cold_layout']-0x0805a000)[0]}
(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'bytes':len(blob),'symbols':manifest['symbols'],'patches':patches},indent=2))
