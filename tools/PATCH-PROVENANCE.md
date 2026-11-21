# Seal Eggs Redux 1.3.5.0+c patch data

Choose the official `Sealegs.1.3.5.0.bin` in the browser patcher and build Redux in one step. Get the firmware from Intellijel and keep a copy for stock recovery. The two existing full Seal Eggs builds remain eligible inputs. [Intellijel updater](https://intellijel.github.io/firmware/) · [Intellijel firmware directory](https://github.com/intellijel/firmware/tree/master/bin)

The page checks the selected image’s length and SHA-256, loads the corresponding difference file from this site and applies it in browser memory. It checks the complete output hash before enabling the download. To install it, select the saved file in the separate WebUSB flasher. To restore stock, select the original Intellijel image there.

| Raw image (589,964 bytes each) | SHA-256 |
| --- | --- |
| Intellijel stock | `ca90eb8f0d7e491d548597fab696bca6d54f30b8bbda5b669c3a426508d8adcf` |
| Seal Eggs full | `62842329515e79bb7c9c0cb3d9a4783c0cb6cd73d66ee6c4021668a0ddc0358b` |
| Seal Eggs full with Tape Bright | `d32d1886689b42c69fa746dd17d9519d63a81026b49dc6e8e85579b9ee7deb86` |
| Tested Seal Eggs Redux 1.3.5.0+c | `0eec5c430a07f188f76a4efe243d1f160b7453ffdf0912da6f56614dbfb6de8f` |

## Published difference files

| Input | Asset | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Official Intellijel 1.3.5.0 | `assets/stock-to-redux.delta` | 163,913 | `1adc7a814b2adc08cc74fa6459ec1d54511926f3019f066591528611e494ff66` |
| Full Seal Eggs with either Tape Bright setting | `assets/redux.delta` | 9,822 | `fb2123d69e6ec0ba2ccb2d6000a91c100537a9cc09dfac42cd1e268a125493f3` |

The direct asset was generated from the verified official firmware and tested Redux release. Its 82 records cover 155,303 changed bytes. This difference includes BRIBERY’s Seal Eggs work, including the Beads adaptation, as well as original Redux changes. Credits and terms are listed in [the third-party notices](../THIRD-PARTY.md).

The compatibility asset is generated from the full non-bright Seal Eggs image and the same Redux release. Its 39 records cover 9,072 changed bytes. Six XOR masks first normalize the optional Tape Bright variant to the verified non-bright base. Both paths produce identical output.

Each record contains an offset, a length and XOR masks. A zero mask represents an unchanged byte, and longer identical runs are omitted. The builder reads only the specified local binary pair. The site supplies the selected patch as a static first-party asset. Firmware files stay on the user’s computer.

Regenerate the assets using Python 3.10 or newer and compare them with the release copies.

```sh
python3 tools/make_delta.py /path/to/Sealegs.1.3.5.0.bin /path/to/Sealegs.1.3.5.0+c.bin /tmp/stock-to-redux.delta
cmp assets/stock-to-redux.delta /tmp/stock-to-redux.delta
python3 tools/make_delta.py /path/to/full-seal-eggs.bin /path/to/Sealegs.1.3.5.0+c.bin /tmp/redux.delta
cmp assets/redux.delta /tmp/redux.delta
```

## Verification

Use Node.js 22 or newer for the JavaScript tests. Supply the local paths to enable the real-image comparison. The tests verify the stock and both Seal Eggs inputs against the same Redux release, independently check every XOR mask, and reject altered inputs and mismatched patch assets.

```sh
SEALEGS_STOCK=/path/to/Sealegs.1.3.5.0.bin \
SEALEGS_BASE=/path/to/full-seal-eggs.bin \
SEALEGS_BRIGHT=/path/to/full-bright-seal-eggs.bin \
SEALEGS_REDUX=/path/to/Sealegs.1.3.5.0+c.bin \
node --test tests/patch.test.mjs tests/transport.test.mjs
```

The transport tests simulate DfuSe erase, write, complete readback and separate restart, including failure cases. The adapter uses the vendored Intellijel updater libraries based on WebDFU by Devan Lai. Original licenses are in `vendor/`. The physical target confirmation matters because other modules share the same STM32 bootloader USB identity. [Intellijel firmware updater source](https://github.com/intellijel/firmware/tree/4201c75802659e42be79bd3c436807ef2f1a8835)
