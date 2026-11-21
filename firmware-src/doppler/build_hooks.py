"""Build the Redux Doppler code and its checked patch manifest."""
from pathlib import Path
import argparse,json,subprocess,struct
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser()
p.add_argument('--origin',type=lambda v:int(v,0),default=0x08058000)
p.add_argument('--mode-address',type=lambda v:int(v,0),default=0x24070404)
p.add_argument('--out',type=Path,required=True)
p.add_argument('--base',type=Path,required=True)
a=p.parse_args();assert a.mode_address==0x24070404,'Update the sharedABI before changing the preference address';a.out.mkdir(parents=True,exist_ok=True)
ld=a.out/'doppler.ld';obj=a.out/'doppler_hooks.o';elf=a.out/'doppler_hooks.elf';raw=a.out/'doppler_hooks.bin'
ld.write_text(f'''SECTIONS {{ . = 0x{a.origin:08x}; .text : {{ *(.text.doppler_hooks) *(.text.doppler_dispatch) *(.text*) *(.rodata*) }} }}\ndoppler_mode_address = 0x{a.mode_address:08x};\n''')
subprocess.run(['arm-none-eabi-gcc','-c','-mcpu=cortex-m7','-mthumb','-mfpu=fpv5-sp-d16','-mfloat-abi=hard',str(ROOT/'doppler_hooks.S'),'-o',str(obj)],check=True)
cobj=a.out/'doppler_dispatch.o'
subprocess.run(['arm-none-eabi-gcc','-c','-Os','-ffreestanding','-fno-builtin','-fno-unwind-tables','-fno-asynchronous-unwind-tables','-mcpu=cortex-m7','-mthumb','-mfpu=fpv5-sp-d16','-mfloat-abi=hard','-I',str(ROOT.parent/'include'),str(ROOT/'doppler_dispatch.c'),'-o',str(cobj)],check=True)
subprocess.run(['arm-none-eabi-ld','-T',str(ld),str(obj),str(cobj),'-o',str(elf)],check=True)
subprocess.run(['arm-none-eabi-objcopy','-O','binary',str(elf),str(raw)],check=True)
syms={}
for l in subprocess.check_output(['arm-none-eabi-nm','-n',str(elf)],text=True).splitlines():
 t=l.split()
 if len(t)==3:syms[t[2]]=int(t[0],16)
def branch(pc,target):
 d=target-(pc+4)
 assert d%2==0 and -(1<<24)<=d<(1<<24)
 v=d&0x1ffffff;s=(v>>24)&1;i1=(v>>23)&1;i2=(v>>22)&1
 return struct.pack('<HH',0xf000|(s<<10)|((v>>12)&0x3ff),0x9000|((1^i1^s)<<13)|((1^i2^s)<<11)|((v>>1)&0x7ff))
patches=[]
for addr,expected,name in [(0x08070886,'f4ee471a','doppler_forward_hook'),(0x0807a670,'b4ee65ba','doppler_reverse_hook')]:
 patches.append({'address':hex(addr),'expected':expected,'bytes':branch(addr,syms[name]).hex(),'reason':name})
base=a.base.read_bytes()
entry=0x080155dc
patches.append({'address':hex(entry),'expected':'5af0ccbf','bytes':branch(entry,syms['doppler_dispatch']).hex(),'reason':'Stock/Smooth/Stepped reader dispatch with state handoff'})
for p in patches:
 off=int(p['address'],16)-0x08000000
 assert base[off:off+4].hex()==p['expected'],p
manifest={'name':'doppler','flash_start':hex(a.origin),'flash_file':str(raw),'kind':'doppler_hooks','origin':hex(a.origin),'mode_address':hex(a.mode_address),'size':len(raw.read_bytes()),'symbols':{k:hex(v) for k,v in syms.items()},'patches':patches,'blob':str(raw)}
(a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(a.out/'doppler_hooks.asm').write_text(subprocess.check_output(['arm-none-eabi-objdump','-d',str(elf)],text=True))
assert len(raw.read_bytes())<=0x2000
print(json.dumps(manifest,indent=2))
