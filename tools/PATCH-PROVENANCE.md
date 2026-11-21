# Seal Eggs Redux 1.3.5.0+c patch data

Start with Intellijel’s original Sealegs 1.3.5.0 file. Use BRIBERY’s patcher to make the full Seal Eggs build with reverse, character, Digi Doppler, Tape pickup, BBD Light, Seal Beads and Seal Microloops. Tape Bright may be enabled or disabled. Select the resulting local .bin in the Redux patcher. [Official firmware](https://github.com/intellijel/firmware/tree/master/bin) · [BRIBERY’s patcher](https://www.thisisbribery.com/sealeggs/)

The page recognizes the firmware by length and SHA-256. The Redux patcher reads a local full Seal Eggs image and applies one small self-hosted difference file in browser memory. Selecting stock in the patcher displays preparation instructions. The separate USB flasher accepts the final Redux image, or official stock for a restore. The user selects the file to write and explicitly starts programming.

| Raw image (589,964 bytes each) | SHA-256 |
| --- | --- |
| Intellijel stock | `ca90eb8f0d7e491d548597fab696bca6d54f30b8bbda5b669c3a426508d8adcf` |
| Seal Eggs full | `62842329515e79bb7c9c0cb3d9a4783c0cb6cd73d66ee6c4021668a0ddc0358b` |
| Seal Eggs full with Tape Bright | `d32d1886689b42c69fa746dd17d9519d63a81026b49dc6e8e85579b9ee7deb86` |
| Tested v0.6, released as 1.3.5.0+c | `0eec5c430a07f188f76a4efe243d1f160b7453ffdf0912da6f56614dbfb6de8f` |

## Public difference file

`assets/redux.delta` is 9,822 bytes. Its SHA-256 is `fb2123d69e6ec0ba2ccb2d6000a91c100537a9cc09dfac42cd1e268a125493f3`. The builder compares only the local full non-bright Seal Eggs image and the local tested Redux release. Each record contains an offset, length and XOR masks. Exactly 9,072 bytes change. Each unchanged byte has a zero mask, and long identical runs are absent. Six additional XOR masks in the patcher normalize the optional Tape Bright variant to the same verified base. The site never reads an upstream patch script, and complete firmware images stay on the user’s computer.

To regenerate the exact asset with Python 3.10 or newer, supply the verified local files.

```sh
python3 tools/make_delta.py /path/to/full-seal-eggs.bin /path/to/tested-v0.6.bin /tmp/redux.delta
cmp assets/redux.delta /tmp/redux.delta
```

## Verification

Use Node.js 22 or newer for the JavaScript tests. Supply the local paths to enable the real-image comparison. It verifies both full Seal Eggs inputs against the same Redux release, independently checks every XOR mask, and confirms that stock is recognized and refused as a direct patch source.

```sh
SEALEGS_STOCK=/path/to/Sealegs.1.3.5.0.bin \
SEALEGS_BASE=/path/to/full-seal-eggs.bin \
SEALEGS_BRIGHT=/path/to/full-bright-seal-eggs.bin \
SEALEGS_REDUX=/path/to/tested-v0.6.bin \
node --test tests/patch.test.mjs tests/transport.test.mjs
```

The transport tests simulate DfuSe erase, write, complete readback and separate restart, including failure cases. The adapter uses the vendored Intellijel updater libraries based on WebDFU by Devan Lai. Original licenses are in `vendor/`. The physical target confirmation matters because other modules share the same STM32 bootloader USB identity. [Intellijel firmware updater source](https://github.com/intellijel/firmware/tree/4201c75802659e42be79bd3c436807ef2f1a8835)
