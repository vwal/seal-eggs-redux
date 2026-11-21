import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {test} from 'node:test';
import {applyRecords, DELTA_SHA, FILES, identify, IMAGE_SIZE, patchRedux, readFirmware} from '../firmware-patch.js';

const buffer = data => data.buffer.slice(data.byteOffset, data.byteOffset + data.byteLength);
const hash = data => createHash('sha256').update(new Uint8Array(data)).digest('hex');
const delta = buffer(await readFile(new URL('../assets/redux.delta', import.meta.url)));
const stockPath = process.env.SEALEGS_STOCK;
const basePath = process.env.SEALEGS_BASE;
const brightPath = process.env.SEALEGS_BRIGHT;
const releasePath = process.env.SEALEGS_REDUX;

test('release delta integrity and record bounds', () => {
  assert.equal(hash(delta), DELTA_SHA);
  assert.equal(delta.byteLength, 9822);
  const mask = new Uint8Array(IMAGE_SIZE);
  applyRecords(mask, delta);
  assert.ok(mask.some(byte => byte !== 0));
  applyRecords(mask, delta);
  assert.ok(mask.every(byte => byte === 0));
});
test('refuses unknown or malformed firmware before device use', async () => {
  for (const input of [new ArrayBuffer(0), new ArrayBuffer(IMAGE_SIZE - 1), new ArrayBuffer(IMAGE_SIZE), new ArrayBuffer(IMAGE_SIZE + 1)]) {
    await assert.rejects(identify(input));
    await assert.rejects(patchRedux(input, delta));
  }
  await assert.rejects(readFirmware({size: 0, arrayBuffer() { throw Error('should not read'); }}), /589,964/);
});
test('invalid headers, truncation and out-of-bounds records', () => {
  for (const input of [new ArrayBuffer(0), new ArrayBuffer(10), delta.slice(0, 7), delta.slice(0, -1)]) {
    assert.throws(() => applyRecords(new Uint8Array(IMAGE_SIZE), input));
  }
  const pastEnd = delta.slice(0);
  new DataView(pastEnd).setUint32(4, IMAGE_SIZE, true);
  assert.throws(() => applyRecords(new Uint8Array(IMAGE_SIZE), pastEnd), /bounds/);
  const overlap = delta.slice(0);
  let second = 4 + 6 + new DataView(overlap).getUint16(8, true);
  new DataView(overlap).setUint32(second, 0, true);
  assert.throws(() => applyRecords(new Uint8Array(IMAGE_SIZE), overlap), /bounds/);
});

test('official stock is recognized for preparation or rollback and cannot be patched directly', {skip: !stockPath}, async () => {
  const stock = buffer(await readFile(stockPath));
  assert.equal((await identify(stock)).id, 'stock');
  await assert.rejects(patchRedux(stock, delta), /Prepare a full Seal Eggs/);
});

test('both allowed local base files produce identical release bytes and the mask contains only Redux differences', {skip: !basePath || !brightPath || !releasePath}, async () => {
  const base = buffer(await readFile(basePath));
  const bright = buffer(await readFile(brightPath));
  const release = buffer(await readFile(releasePath));
  assert.equal((await identify(base)).id, 'eggs');
  assert.equal((await identify(bright)).id, 'bright');
  for (const input of [base, bright]) {
    const initial = hash(input);
    const output = await patchRedux(input, delta);
    assert.deepEqual(new Uint8Array(output), new Uint8Array(release));
    assert.equal(hash(output), FILES.redux.hash);
    assert.equal(hash(input), initial);
  }

  const invalid = base.slice(0);
  new Uint8Array(invalid)[1234] ^= 1;
  await assert.rejects(patchRedux(invalid, delta), /Unrecognized SHA/);
  const badDelta = delta.slice(0);
  new Uint8Array(badDelta)[42] ^= 1;
  await assert.rejects(patchRedux(base, badDelta), /patch data failed/);
  await assert.rejects(patchRedux(release, delta), /already matches/);

  const mask = new Uint8Array(IMAGE_SIZE);
  applyRecords(mask, delta);
  const src = new Uint8Array(base);
  const alt = new Uint8Array(bright);
  const dst = new Uint8Array(release);
  let changed = 0;
  let brightChanges = 0;
  for (let i = 0; i < IMAGE_SIZE; i++) {
    assert.equal(mask[i], src[i] ^ dst[i]);
    changed += mask[i] !== 0;
    brightChanges += src[i] !== alt[i];
  }
  assert.equal(changed, 9072);
  assert.equal(brightChanges, 6);
});
