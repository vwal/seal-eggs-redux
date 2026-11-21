from pathlib import Path
import subprocess,json,struct,argparse,hashlib
D=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();O=args.output.resolve();O.mkdir(parents=True,exist_ok=True)
base=args.base.read_bytes()
assert hashlib.sha256(base).hexdigest()=='62842329515e79bb7c9c0cb3d9a4783c0cb6cd73d66ee6c4021668a0ddc0358b', 'Unsupported base: require pinned full SealEggs no-bright binary'
flags=['-mcpu=cortex-m7','-mthumb','-mfpu=fpv5-d16','-mfloat-abi=hard','-Os','-ffreestanding','-fno-builtin','-ffunction-sections','-fdata-sections','-fno-unwind-tables','-fno-asynchronous-unwind-tables','-Wall','-Wextra','-Werror']
for f in ['options.c','hooks.S']:
 subprocess.run(['arm-none-eabi-gcc',*flags,*(['-mgeneral-regs-only'] if f.endswith('.c') else []),'-c',str(D/f),'-o',str(O/(f+'.o'))],check=True)
subprocess.run(['arm-none-eabi-gcc',*flags,'-nostdlib','-Wl,--build-id=none','-T',str(D/'link.ld'),str(O/'options.c.o'),str(O/'hooks.S.o'),'-o',str(O/'options.elf')],check=True)
subprocess.run(['arm-none-eabi-objcopy','-O','binary',str(O/'options.elf'),str(O/'options.bin')],check=True)
symbols={}
for line in subprocess.check_output(['arm-none-eabi-nm','--defined-only',str(O/'options.elf')],text=True).splitlines():
 p=line.split()
 if len(p)==3:symbols[p[2]]=int(p[0],16)
(O/'symbols.json').write_text(json.dumps(symbols,indent=2)+'\n')
def branch(a,b):
 imm=b-(a+4)
 assert imm%2==0 and -(1<<24)<=imm<(1<<24)
 v=imm&0x1ffffff;s=(v>>24)&1;i1=(v>>23)&1;i2=(v>>22)&1
 return struct.pack('<HH',0xf000|(s<<10)|((v>>12)&0x3ff),0x9000|((1^(i1^s))<<13)|((1^(i2^s))<<11)|((v>>1)&0x7ff))
items=[(0x080087d8,'options_dispatch','Own button samples only while options is open'),(0x08076000,'options_character_hook','Existing long Character gesture updates per-model persistent preference'),(0x08076036,'options_write_hook','Write versioned preferences before stock settings checksum'),(0x0807604e,'options_load_hook','Read only checksum-validated versioned preference record'),(0x0801dca6,'options_save_done_hook','Acknowledge only completed native header and record writes'),(0x08075120,'options_led_freeze','FREEZE option RGB override'),(0x08075140,'options_led_tap','TAP option RGB override'),(0x08075160,'options_led_delay','DELAY option RGB override'),(0x08075180,'options_led_mod','MOD option/status RGB override'),(0x080751c0,'options_led_tap_secondary','TAP normal-display RGB override')]
patches=[]
items.append((0x0800cebe,'options_led_tap_pulse','Suppress native TAP pulse colour only while the options layer owns its indicator'))
for a,s,reason in items:patches.append({'address':hex(a),'expected':base[a-0x08000000:a-0x08000000+4].hex(),'bytes':branch(a,symbols[s]).hex(),'reason':reason})
manifest={'name':'options','flash_start':'0x0805e000','flash_file':str(O/'options.bin'),'patches':patches}
(O/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'bytes':(O/'options.bin').stat().st_size,'symbols':{k:hex(v) for k,v in symbols.items() if k.startswith('options_')}},indent=2))
