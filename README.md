# Seal Eggs Redux · 1.3.5.0+c

[Open the patcher, USB updater and printable guides](https://vwal.github.io/seal-eggs-redux/)

Independent community firmware for Intellijel Sealegs. Redux adds per-model settings that survive power-off, continuous Smooth Doppler, a two-second stereo Pitch Throw with quiet TIME/L repositioning, two additional Seal Beads recording qualities and native Digi timing diagnostics. It builds on BRIBERY’s live reverse, model-specific Character sounds, tape and BBD voicings, original Stepped Doppler, Seal Beads and Microloops.

## Install

1. Download the original `Sealegs.1.3.5.0.bin` from [Intellijel’s firmware directory](https://github.com/intellijel/firmware/tree/master/bin). Keep a copy for recovery.
2. Select the original file in the [Redux patcher](https://vwal.github.io/seal-eggs-redux/#patcher). It applies BRIBERY’s Seal Eggs features and the Redux additions in one step on your computer. Save `Sealegs.1.3.5.0+c.bin` and the accompanying [firmware credits and licenses](FIRMWARE-NOTICES.txt).
3. Select the saved Redux file in the [USB flasher](https://vwal.github.io/seal-eggs-redux/#flasher) and follow its instructions. Use desktop Chrome or Edge with a USB data cable.

The official file and both previously supported full Seal Eggs builds (Tape Bright on or off) produce the same 589,964-byte release. The patcher verifies the input, the difference file and the output before enabling download. The release SHA-256 is `0eec5c430a07f188f76a4efe243d1f160b7453ffdf0912da6f56614dbfb6de8f`. The site distributes difference files generated for Redux. Modified firmware is provided as is and installed at your own risk.

## Back to the stock firmware

To restore the official firmware, open the [Intellijel Firmware Updater](https://intellijel.github.io/firmware/), select **Sealegs** and follow the instructions to reflash your module.

## Publications

| Guide | US Letter | A4 |
| --- | --- | --- |
| Full stock and Redux quick reference | [Letter](docs/sealegs-redux-quick-reference-letter.pdf) | [A4](docs/sealegs-redux-quick-reference-a4.pdf) |
| New features quick card | [Letter](docs/sealegs-redux-new-features-letter.pdf) | [A4](docs/sealegs-redux-new-features-a4.pdf) |
| Detailed feature reference | [Letter](docs/sealegs-redux-feature-reference-letter.pdf) | [A4](docs/sealegs-redux-feature-reference-a4.pdf) |

## Source and verification

- [Rebuild the firmware from Redux source](firmware-src/README.md)
- [Generate the browser delta and run patch and simulated USB tests](tools/PATCH-PROVENANCE.md)
- [PDF generator and content](tools/docs/)
- To preview locally, run `python3 -m http.server --bind 127.0.0.1` in the repository root and open the printed localhost address.

## Credits and license

BRIBERY created [Seal Eggs](https://www.thisisbribery.com/sealeggs/). His work is available under [PolyForm Noncommercial 1.0.0 with additional permissions for paid music-making and for Intellijel](notices/Seal-Eggs-LICENSE.md). Seal Beads incorporates [Émilie Gillet’s Beads and stmlib](https://github.com/pichenettes/eurorack) under MIT. Intellijel made Sealegs and publishes the original firmware and updater. [Third-party notices](THIRD-PARTY.md).

Required Notice: Copyright 2026 Bribery (https://thisisbribery.com)

Original Redux additions are free to use, modify and share under the [Redux Attribution – No Sale License](LICENSE.txt). Its Intellijel exception covers vwal’s own firmware changes. This project contains carefully tested AI-generated code. [Buy Me a Coffee](https://www.buymeacoffee.com/vwal).
