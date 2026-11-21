/** Release pins for raw files. 1.3.5.0+c is the hardware-tested v0.6 binary. */
export const IMAGE_SIZE = 589964;
export const OUTPUT_NAME = 'Sealegs.1.3.5.0+c.bin';
export const DELTA_SHA = 'fb2123d69e6ec0ba2ccb2d6000a91c100537a9cc09dfac42cd1e268a125493f3';
export const FILES = Object.freeze({
  stock: {name: 'Intellijel Sealegs 1.3.5.0', hash: 'ca90eb8f0d7e491d548597fab696bca6d54f30b8bbda5b669c3a426508d8adcf'},
  eggs: {name: 'Seal Eggs, full build', hash: '62842329515e79bb7c9c0cb3d9a4783c0cb6cd73d66ee6c4021668a0ddc0358b'},
  bright: {name: 'Seal Eggs, full build with Tape Bright', hash: 'd32d1886689b42c69fa746dd17d9519d63a81026b49dc6e8e85579b9ee7deb86'},
  redux: {name: 'Seal Eggs Redux 1.3.5.0+c', hash: '0eec5c430a07f188f76a4efe243d1f160b7453ffdf0912da6f56614dbfb6de8f'},
});

async function digest(bytes) {
  const hash = await crypto.subtle.digest('SHA-256', bytes);
  return Array.from(new Uint8Array(hash), byte => byte.toString(16).padStart(2, '0')).join('');
}

export async function identify(input) {
  if (!(input instanceof ArrayBuffer) || input.byteLength !== IMAGE_SIZE) {
    throw new Error('Choose a raw 589,964-byte Sealegs 1.3.5.0 .bin file.');
  }
  const buffer = input.slice(0);
  const hash = await digest(buffer);
  const id = Object.keys(FILES).find(key => FILES[key].hash === hash);
  if (!id) throw new Error('Unrecognized SHA-256. Check the firmware version and build against the listed supported files.');
  return {id, name: FILES[id].name, hash, buffer};
}

export async function readFirmware(file) {
  if (!file || file.size !== IMAGE_SIZE) throw new Error('Choose a raw 589,964-byte Sealegs .bin file.');
  return identify(await file.arrayBuffer());
}

// These six XOR masks express the complete difference between the two
// supported Seal Eggs variants. Normalize Bright before applying the same delta.
function normalizeBright(bytes) {
  bytes[0x11308] ^= 0x33;
  bytes[0x11309] ^= 0x33;
  bytes[0x1130a] ^= 0xc3;
  bytes[0x1130b] ^= 0xc0;
  bytes[0x1136a] ^= 0x40;
  bytes[0x1136b] ^= 0x40;
}

export function applyRecords(bytes, delta) {
  const records = new DataView(delta);
  if (delta.byteLength < 4 || records.getUint32(0) !== 0x53525831) throw new Error('Unknown Redux patch format.');
  let cursor = 4;
  let lastEnd = 0;
  while (cursor < delta.byteLength) {
    if (delta.byteLength - cursor < 6) throw new Error('Truncated Redux record.');
    const start = records.getUint32(cursor, true);
    const length = records.getUint16(cursor + 4, true);
    cursor += 6;
    if (length === 0 || start < lastEnd || start + length > bytes.length || cursor + length > delta.byteLength) {
      throw new Error('Invalid Redux record bounds.');
    }
    for (let i = 0; i < length; i++) bytes[start + i] ^= records.getUint8(cursor + i);
    lastEnd = start + length;
    cursor += length;
  }
}

export async function patchRedux(input, deltaInput) {
  const source = await identify(input);
  if (source.id === 'redux') throw new Error('This file already matches Seal Eggs Redux 1.3.5.0+c.');
  if (source.id === 'stock') throw new Error('Prepare a full Seal Eggs base with BRIBERY’s patcher first.');
  const bytes = new Uint8Array(source.buffer);
  if (source.id === 'bright') normalizeBright(bytes);
  if (await digest(bytes) !== FILES.eggs.hash) throw new Error('The intermediate Seal Eggs image failed verification.');
  const delta = deltaInput?.slice(0);
  if (!(delta instanceof ArrayBuffer) || delta.byteLength !== 9822 || await digest(delta) !== DELTA_SHA) throw new Error('The Redux patch data failed verification.');
  applyRecords(bytes, delta);
  if (await digest(bytes) !== FILES.redux.hash) throw new Error('The finished firmware failed its SHA-256 check.');
  return bytes.buffer;
}
