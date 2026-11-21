import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {test} from 'node:test';
import {applyRecords, DELTA_SHA, FILES, identify, IMAGE_SIZE, patchFor, patchRedux, readFirmware} from '../firmware-patch.js';

const buffer = data => data.buffer.slice(data.byteOffset, data.byteOffset + data.byteLength);
const hash = data => createHash('sha256').update(new Uint8Array(data)).digest('hex');
const delta = buffer(await readFile(new URL('../assets/redux.delta', import.meta.url)));
const stockDelta = buffer(await readFile(new URL('../assets/stock-to-redux.delta', import.meta.url)));
const stockPath = process.env.SEALEGS_STOCK;
const basePath = process.env.SEALEGS_BASE;
const brightPath = process.env.SEALEGS_BRIGHT;
const releasePath = process.env.SEALEGS_REDUX;

function verifyMask(source, target, patch, expectedChanges) {
  const mask = new Uint8Array(IMAGE_SIZE);
  applyRecords(mask, patch);
  const before = new Uint8Array(source);
  const after = new Uint8Array(target);
  let changed = 0;
  for (let i = 0; i < IMAGE_SIZE; i++) {
    assert.equal(mask[i], before[i] ^ after[i]);
    changed += mask[i] !== 0;
  }
  assert.equal(changed, expectedChanges);
}

test('stock and compatibility assets match the release pins and bounds', () => {
  assert.equal(hash(delta), DELTA_SHA);
  for (const [sourceId, data] of [['stock', stockDelta], ['eggs', delta], ['bright', delta]]) {
    const patch = patchFor(sourceId);
    assert.equal(hash(data), patch.hash);
    assert.equal(data.byteLength, patch.size);
    const mask = new Uint8Array(IMAGE_SIZE);
    applyRecords(mask, data);
    assert.ok(mask.some(byte => byte !== 0));
    applyRecords(mask, data);
    assert.ok(mask.every(byte => byte === 0));
  }
  assert.throws(() => patchFor('redux'));
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

test('official stock patches directly to the tested release and its original bytes remain intact', {skip: !stockPath || !releasePath}, async () => {
  const stock = buffer(await readFile(stockPath));
  const release = buffer(await readFile(releasePath));
  assert.equal((await identify(stock)).id, 'stock');
  const output = await patchRedux(stock, stockDelta);
  assert.deepEqual(new Uint8Array(output), new Uint8Array(release));
  assert.equal(hash(output), FILES.redux.hash);
  assert.equal(hash(stock), FILES.stock.hash);
  verifyMask(stock, release, stockDelta, 155303);
  await assert.rejects(patchRedux(stock, delta), /patch data failed/);
  const corrupt = stockDelta.slice(0);
  new Uint8Array(corrupt)[100] ^= 1;
  await assert.rejects(patchRedux(stock, corrupt), /patch data failed/);
  const changedInput = stock.slice(0);
  new Uint8Array(changedInput)[100] ^= 1;
  await assert.rejects(patchRedux(changedInput, stockDelta), /Unrecognized SHA/);
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

  verifyMask(base, release, delta, 9072);
  await assert.rejects(patchRedux(base, stockDelta), /patch data failed/);
  const normal = new Uint8Array(base);
  const alt = new Uint8Array(bright);
  assert.equal(normal.reduce((count, byte, i) => count + Number(byte !== alt[i]), 0), 6);
});
