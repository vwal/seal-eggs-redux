# Seal Eggs Redux · 1.3.5.0+c

[Open the patcher, USB updater and printable guides](https://vwal.github.io/seal-eggs-redux/)

Independent community firmware for Intellijel Sealegs. Redux adds per-model settings that survive power-off, continuous Smooth Doppler, a two-second stereo Pitch Throw with quiet TIME/L repositioning, two additional Seal Beads recording qualities and native Digi timing diagnostics. It builds on BRIBERY’s live reverse, model-specific Character sounds, tape and BBD voicings, original Stepped Doppler, Seal Beads and Microloops.

## Install

1. Obtain the [original Sealegs.1.3.5.0.bin](https://intellijel.github.io/firmware/) from [Intellijel’s firmware directory](https://github.com/intellijel/firmware/tree/master/bin). Keep a copy for recovery.
2. At [BRIBERY’s Seal Eggs patcher](https://www.thisisbribery.com/sealeggs/), enable Live reverse, Character, Digi Doppler, Tape pickup, BBD Light, Seal Beads and Seal Microloops. Save the full build. Both Tape Bright choices are supported by the Redux web patcher.
3. Choose that local Seal Eggs file in the [Redux patcher](https://vwal.github.io/seal-eggs-redux/#patcher). Download the verified result, then select the saved file in the USB section. Only this final image needs to be installed.

Both full Seal Eggs variants produce the same 589,964-byte Redux 1.3.5.0+c release. Its SHA-256 is `0eec5c430a07f188f76a4efe243d1f160b7453ffdf0912da6f56614dbfb6de8f`. The site supplies a 9,822-byte difference file for the Redux step. It contains no complete firmware image or upstream patch dataset. Patching runs locally. Flashing uses desktop Chrome or Edge and a USB data cable. Follow the on-page instructions. Modified firmware is provided as is and installed at your own risk.

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

BRIBERY created [Seal Eggs](https://www.thisisbribery.com/sealeggs/). Seal Beads incorporates [Émilie Gillet’s Beads and stmlib](https://github.com/pichenettes/eurorack) under MIT. Intellijel made Sealegs and publishes the original firmware and updater. [Third-party notices](THIRD-PARTY.md).

Original Redux additions are free to use, modify and share under the [Redux Attribution – No Sale License](LICENSE.txt), including an official Intellijel commercial-integration exception for vwal’s original firmware changes in the Redux delta over Seal Eggs. BRIBERY’s code and all other third-party components require their own applicable permissions. This project contains carefully tested AI-generated code. [Buy Me a Coffee](https://www.buymeacoffee.com/vwal).
