# Build Seal Eggs Redux 1.3.5.0+c

These are the firmware sources for the Redux additions to Intellijel Sealegs.
Release 1.3.5.0+c has the same bytes as development build v0.6.

## Developer build input

Start with the official Intellijel file and run BRIBERY’s patcher before applying Redux. The public Redux patcher takes the resulting full Seal Eggs image. The source build below uses the same non-Bright image as its link and patch baseline.

Download [Sealegs.1.3.5.0.bin from Intellijel](https://github.com/intellijel/firmware/blob/master/bin/Sealegs.1.3.5.0.bin).
Use [BRIBERY’s Seal Eggs patcher](https://www.thisisbribery.com/sealeggs/) with Live reverse, Character, Digi Doppler, Tape pickup, BBD Light, Seal Beads and Seal Microloops enabled. Leave Tape Bright off. Save the generated Seal Eggs file beside your local checkout or in a separate directory.

The source build targets this non-Bright image. Its SHA-256 is
`62842329515e79bb7c9c0cb3d9a4783c0cb6cd73d66ee6c4021668a0ddc0358b`.

## Reproduce the release

Use Python 3.10 or later and the GNU Arm bare-metal toolchain. The verified
build used `arm-none-eabi-gcc` 16.2.0 and GNU binutils 2.47.20260726.
Place the compiler, assembler, linker, `objcopy`, `objdump` and `nm`
for the `arm-none-eabi` target on PATH. The Python scripts use the standard library.

From the repository root, substitute the path to your generated Seal Eggs image and choose a separate output directory outside the checkout.

```sh
python3 firmware-src/build.py --base "/path/to/your/Seal-Eggs.bin" --output "../redux-build"
```

The builder verifies the input hash, compiles the six components and checks their flash reservations and hook locations. It verifies the complete output against the release hash before writing `Sealegs.1.3.5.0+c.bin`. The output directory also contains component files and a build report. The final image is 589,964 bytes.

```text
0eec5c430a07f188f76a4efe243d1f160b7453ffdf0912da6f56614dbfb6de8f
```

## Source and attribution

| Directory | Redux component |
| --- | --- |
| `options/` | MOD SYNC settings layer, LED feedback and saved model preferences |
| `native/` | Runtime Tape tone and pickup selection, and BBD filter selection |
| `doppler/` | Digi reader selection and continuous pitch response |
| `throw/` | One-way pitch echo, slider recharge and soft pickup |
| `sunny/` | Seal Beads quality selection, control scaling and Cold sample-rate conversion |
| `diagnostics/` | Native Digi processing-time indicators |

The developer build input supplies Intellijel’s firmware, BRIBERY’s Seal Eggs engines and the Beads/stmlib components by Émilie Gillet. The public Redux delta is derived from the supported Seal Eggs baseline and the tested Redux output. BRIBERY supplies his patch through his own site. The original Redux additions are covered by the [release license](../LICENSE.txt). Upstream rights remain with their respective authors. The [upstream MIT notice](https://github.com/thisisbribery/SealEggs_v1/blob/c0cc7ed821a3285c926a9d77709daece2b800745/LICENSE-beads.txt) covers the Beads/stmlib portions. A generated image contains those third-party works and the manufacturer’s firmware. Keep the generated files local.
