import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';
import {test} from 'node:test';

for (const name of ['dfu', 'dfuse']) {
  vm.runInThisContext(await readFile(new URL(`../vendor/${name}.js`, import.meta.url), 'utf8'));
}
const {connectSealegs, flashSealegs, restartSealegs, disconnectSealegs} = await import('../transport.js');
const BASE = 0x08000000, LENGTH = 589964, PAGE = 128 * 1024;
const MAP = '@Internal Flash /0x08000000/08*128Kg';

function view(bytes) {
  const a = Uint8Array.from(bytes);
  return new DataView(a.buffer);
}
function image() {
  const a = Uint8Array.from({length: LENGTH}, (_, i) => (i * 29 + (i >>> 9)) & 255);
  const d = new DataView(a.buffer);
  d.setUint32(0, 0x20020000, true);
  d.setUint32(4, 0x0802be39, true);
  return a.buffer;
}

// Stateful fake implementing the relevant AN3156 state transitions and current
// request-length address formula. It deliberately uses cfg=3, interface=7,
// alternate=2 to catch assumptions copied from common STM32 descriptors.
class FakeUSBDevice {
  constructor(options = {}) {
    this.options = options;
    this.vendorId = options.vendorId ?? 0x0483;
    this.productId = options.productId ?? 0xdf11;
    this.productName = 'Fake STM32 DFU';
    this.serialNumber = 'TEST-ONLY';
    this.map = options.map ?? MAP;
    this.calls = [];
    this.memory = new Uint8Array(1024 * 1024).fill(0x55);
    this.opened = false;
    this.configuration = null;
    this.state = options.initialState ?? 2;
    this.pointer = BASE;
    this.pending = null;
    this.hasWritten = false;
    this.uploadOccurred = false;
    const alt = {alternateSetting: 2, interfaceClass: 0xfe, interfaceSubclass: 1,
      interfaceProtocol: 2, interfaceName: options.missingNames ? null : this.map};
    const iface = {interfaceNumber: 7, alternate: alt, alternates: [alt], claimed: false};
    if (options.ambiguous) iface.alternates.push({...alt, alternateSetting: 3});
    this.configurations = [{configurationValue: 3, interfaces: [iface]}];
    const parts = [9, 2, 0, 0, 1, 3, 0, 0x80, 50];
    for (const a of iface.alternates) parts.push(9, 4, 7, a.alternateSetting, 0, 0xfe, 1, 2, 1);
    const transfer = options.transferSize ?? 2048;
    const version = options.version ?? 0x011a;
    parts.push(9, 0x21, options.attributes ?? 3, 0, 0, transfer & 255, transfer >> 8, version & 255, version >> 8);
    parts[2] = parts.length;
    this.configDescriptor = Uint8Array.from(parts);
    if (options.malformedDescriptor) this.configDescriptor[9] = 0;
    this.strings = new Map([[0, Uint8Array.from([4, 3, 9, 4])]]);
    const chars = [...this.map].flatMap(c => [c.charCodeAt(0), 0]);
    this.strings.set(1, Uint8Array.from([chars.length + 2, 3, ...chars]));
  }
  async open() { this.opened = true; this.calls.push(['open']); }
  async close() { this.opened = false; this.calls.push(['close']); }
  async selectConfiguration(value) {
    assert.equal(value, 3); this.configuration = this.configurations[0]; this.calls.push(['configuration', value]);
  }
  async claimInterface(number) { assert.equal(number, 7); this.configuration.interfaces[0].claimed = true; this.calls.push(['claim', number]); }
  async selectAlternateInterface(number, alt) {
    assert.equal(number, 7);
    this.configuration.interfaces[0].alternate = this.configuration.interfaces[0].alternates.find(a => a.alternateSetting === alt);
    this.calls.push(['alternate', alt]);
  }
  async controlTransferIn(setup, length) {
    if (setup.requestType === 'standard') {
      this.calls.push(['descriptor', setup.value, length]);
      const type = setup.value >> 8;
      const bytes = type === 2 ? this.configDescriptor : this.strings.get(setup.value & 255);
      return {status: 'ok', data: view(bytes.slice(0, length))};
    }
    assert.equal(setup.index, 7);
    this.calls.push(['in', setup.request, setup.value, length]);
    if (setup.request === 3) {
      assert.equal(length, 6);
      if (this.options.hangStatus) return new Promise(() => {});
      if (this.options.statusUSBError) return {status: 'stall', data: null};
      if (this.options.errorOnUpload && this.uploadOccurred) return {status: 'ok', data: view([15, 0, 0, 0, 10, 0])};
      if (this.pending) {
        const pending = this.pending;
        const kind = this.pendingKind;
        this.pending = null;
        pending();
        this.state = 5;
        if (this.options.errorOnCommand || (this.options.errorOnErase && kind === 'erase') || (this.options.errorOnWrite && kind === 'write')) {
          return {status: 'ok', data: view([3, 0, 0, 0, 10, 0])};
        }
        if (this.options.longBusy) return {status: 'ok', data: view([0, 255, 255, 255, 4, 0])};
        if (this.options.wrongDownloadState) this.state = 2;
        if (this.options.busyOnce) {
          this.options.busyOnce = false;
          return {status: 'ok', data: view([0, 1, 0, 0, 4, 0])};
        }
      }
      if (this.state === 6) {
        if (this.options.restartDisconnect) {
          this.manager.emit('disconnect', {device: this});
          throw new Error('Device disconnected during manifestation');
        }
        if (this.options.restartError) throw new Error('Unexplained manifestation USB error');
        this.state = 7;
      }
      return {status: 'ok', data: view([0, 0, 0, 0, this.state, 0])};
    }
    if (setup.request === 2) {
      assert.ok([2, 9].includes(this.state), `UPLOAD requires idle, got ${this.state}`);
      assert.ok(setup.value >= 2);
      const address = this.pointer + (setup.value - 2) * length;
      this.calls.push(['upload', address, length, setup.value]);
      this.uploadOccurred = true;
      if (this.options.rejectUpload) return {status: 'stall', data: null};
      const bytes = this.memory.slice(address - BASE, address - BASE + length);
      if (this.options.corruptReadback) bytes[0] ^= 1;
      this.state = 9;
      const short = this.options.shortUpload || (this.options.shortUploadAfterWrite && this.hasWritten);
      return {status: 'ok', data: view(short ? bytes.slice(0, -1) : bytes)};
    }
    assert.fail(`Forbidden/unimplemented IN request ${setup.request}`);
  }
  async controlTransferOut(setup, data) {
    assert.equal(setup.requestType, 'class');
    assert.equal(setup.recipient, 'interface');
    assert.equal(setup.index, 7);
    this.calls.push(['out', setup.request, setup.value, data.byteLength]);
    if (setup.request === 6) {
      assert.ok([2, 5, 9].includes(this.state), `ABORT invalid from ${this.state}`);
      assert.equal(data.byteLength, 0);
      this.state = 2;
      return {status: 'ok', bytesWritten: 0};
    }
    assert.equal(setup.request, 1, 'No DETACH, CLRSTATUS or unprotect command is allowed');
    assert.ok([2, 5].includes(this.state), `DNLOAD invalid from ${this.state}`);
    const bytes = new Uint8Array(data);
    if (setup.value === 0) {
      if (!bytes.length) {
        this.calls.push(['manifest']);
        this.state = 6;
      } else {
        assert.equal(bytes.length, 5, 'Commands always include a four-byte address: never mass erase');
        const address = new DataView(data).getUint32(1, true);
        assert.ok([0x21, 0x41].includes(bytes[0]), 'No read-unprotect command');
        this.calls.push([bytes[0] === 0x41 ? 'erase' : 'address', address]);
        this.pendingKind = bytes[0] === 0x41 ? 'erase' : 'address';
        this.pending = () => {
          if (bytes[0] === 0x41) this.memory.fill(0xff, address - BASE, address - BASE + PAGE);
          else this.pointer = address;
        };
        this.state = 3;
      }
    } else {
      assert.equal(setup.value, 2);
      assert.equal(this.state, 5);
      this.calls.push(['write', this.pointer, bytes.length]);
      this.pendingKind = 'write';
      this.pending = () => { this.memory.set(bytes, this.pointer - BASE); this.hasWritten = true; };
      this.state = 3;
      if (this.options.shortWrite) return {status: 'ok', bytesWritten: bytes.length - 4};
    }
    return {status: 'ok', bytesWritten: bytes.length};
  }
}

function fakeEnvironment(options) {
  const device = new FakeUSBDevice(options);
  const listeners = new Map();
  const manager = {
    async requestDevice(query) { assert.deepEqual(query.filters, [{vendorId: 0x0483, productId: 0xdf11}]); return device; },
    addEventListener(event, fn) { const set = listeners.get(event) || new Set(); set.add(fn); listeners.set(event, set); },
    removeEventListener(event, fn) { listeners.get(event)?.delete(fn); },
    emit(event, value) { for (const fn of listeners.get(event) || []) fn(value); },
  };
  device.manager = manager;
  Object.defineProperty(globalThis, 'navigator', {configurable: true, value: {usb: manager}});
  return device;
}
function mutations(device) { return device.calls.filter(c => ['erase', 'write', 'manifest'].includes(c[0])); }

for (const transferSize of [1024, 2048]) {
  test(`complete write/readback at ${transferSize} bytes; explicit restart only`, async () => {
    const usb = fakeEnvironment({transferSize, missingNames: true, busyOnce: true});
    const s = await connectSealegs();
    assert.equal(s.interfaceNumber, 7);
    assert.equal(s.configurationValue, 3);
    assert.equal(s.alternateSetting, 2);
    assert.equal(s.sectorCount, 5);
    assert.equal(s.eraseEnd, BASE + 5 * PAGE);
    const data = image();
    const progress = [];
    const result = await flashSealegs(s, data, p => progress.push(p));
    assert.equal(result.bytesVerified, LENGTH);
    assert.equal(s.state, 'verified');
    assert.equal(s.verified, true);
    assert.equal(usb.state, 2, 'leave ROM in idle');
    assert.deepEqual(usb.memory.slice(0, LENGTH), new Uint8Array(data));
    assert.ok(usb.memory.slice(LENGTH, 5 * PAGE).every(x => x === 0xff));
    assert.ok(usb.memory.slice(5 * PAGE).every(x => x === 0x55), 'never erase beyond final intersecting sector');
    assert.deepEqual(usb.calls.filter(c => c[0] === 'erase').map(c => c[1]), Array.from({length: 5}, (_, i) => BASE + i * PAGE));
    const uploads = usb.calls.filter(c => c[0] === 'upload');
    assert.deepEqual(uploads.shift(), ['upload', BASE, 8, 2], 'check actual read access before erasing');
    for (let i = 0; i < uploads.length; i++) {
      assert.equal(uploads[i][1], BASE + i * transferSize);
      assert.equal(uploads[i][3], 2);
    }
    assert.deepEqual(uploads.at(-1), ['upload', BASE + LENGTH - 140, 140, 2]);
    assert.ok(!usb.calls.some(c => c[0] === 'manifest'));
    assert.deepEqual(progress.at(-1), {phase: 'verify', done: LENGTH, total: LENGTH});
    const restart = await restartSealegs(s);
    assert.equal(restart.restartRequested, true);
    assert.equal(s.state, 'restarted');
    assert.equal(usb.calls.filter(c => c[0] === 'manifest').length, 1);
    await disconnectSealegs(s);
  });
}

test('invalid file length/vectors cause no USB requests and no erases', async () => {
  const usb = fakeEnvironment();
  const s = await connectSealegs();
  const count = usb.calls.length;
  await assert.rejects(flashSealegs(s, new ArrayBuffer(8)), /589964/);
  const invalid = image(); new DataView(invalid).setUint32(4, 0x08000001, true);
  await assert.rejects(flashSealegs(s, invalid), /vectors/);
  assert.equal(usb.calls.length, count);
  assert.equal(mutations(usb).length, 0);
  await assert.rejects(restartSealegs(s), /verified/);
  await disconnectSealegs(s);
});

for (const [label, options] of [
  ['wrong VID', {vendorId: 1}], ['wrong PID', {productId: 1}],
  ['wrong protocol version', {version: 0x0110}], ['no upload', {attributes: 1}],
  ['no download', {attributes: 2}], ['ambiguous internal flash', {ambiguous: true}],
  ['unsupported chunk size', {transferSize: 4096}], ['unaligned chunk size', {transferSize: 1023}],
  ['short memory map', {map: '@Internal Flash /0x08000000/04*128Kg'}],
  ['memory gap', {map: '@Internal Flash /0x08000000/02*128Kg/0x08060000/04*128Kg'}],
  ['overlapping map', {map: '@Internal Flash /0x08000000/04*128Kg/0x08040000/04*128Kg'}],
  ['read-only final sector', {map: '@Internal Flash /0x08000000/04*128Kg,04*128Ka'}],
  ['trailing garbage', {map: MAP + '/garbage'}], ['malformed descriptor', {malformedDescriptor: true}],
  ['DFU error on connect', {initialState: 10}], ['active download on connect', {initialState: 5}],
]) {
  test(`reject ${label} before any erase`, async () => {
    const usb = fakeEnvironment(options);
    await assert.rejects(connectSealegs());
    assert.equal(mutations(usb).length, 0);
    assert.equal(usb.calls.filter(c => c[0] === 'out').length, 0);
  });
}

for (const [label, option, message] of [
  ['short write', 'shortWrite', /short/], ['short readback', 'shortUploadAfterWrite', /short/],
  ['corrupt readback', 'corruptReadback', /mismatch/], ['DFU command error', 'errorOnCommand', /DFU reported error/],
  ['DFU erase error', 'errorOnErase', /DFU reported error/], ['DFU data-write error', 'errorOnWrite', /DFU reported error/],
  ['excessive busy deadline', 'longBusy', /polling deadline/],
  ['wrong state', 'wrongDownloadState', /Unexpected DFU state/], ['USB stall', 'statusUSBError', /USB read failed/],
]) {
  test(`stop after ${label}; never retry, clear protection or restart`, async () => {
    const usb = fakeEnvironment();
    const s = await connectSealegs();
    usb.options[option] = true;
    await assert.rejects(flashSealegs(s, image()), message);
    assert.equal(s.state, 'failed');
    assert.equal(s.verified, false);
    if (['shortUploadAfterWrite', 'corruptReadback'].includes(option)) assert.equal(usb.hasWritten, true, 'exercise readback failure after actual write phase');
    if (option === 'errorOnErase') {
      assert.equal(usb.calls.filter(c => c[0] === 'erase').length, 1);
      assert.equal(usb.calls.filter(c => c[0] === 'write').length, 0);
    }
    if (option === 'errorOnWrite') assert.equal(usb.calls.filter(c => c[0] === 'write').length, 1);
    assert.ok(!usb.calls.some(c => c[0] === 'manifest'));
    const calls = usb.calls.length;
    await assert.rejects(flashSealegs(s, image()), /not ready/);
    await assert.rejects(restartSealegs(s), /verified/);
    assert.equal(usb.calls.length, calls);
    await disconnectSealegs(s);
  });
}

for (const option of ['shortUpload', 'rejectUpload', 'errorOnUpload']) {
  test(`preflight ${option} prevents every erase and write`, async () => {
    const usb = fakeEnvironment();
    const s = await connectSealegs();
    usb.options[option] = true;
    await assert.rejects(flashSealegs(s, image()));
    assert.equal(mutations(usb).length, 0);
    assert.equal(s.state, 'failed');
    assert.equal(s.verified, false);
    await disconnectSealegs(s);
  });
}

test('USB timeout poisons session without retry; close remains available', async () => {
  const usb = fakeEnvironment();
  const s = await connectSealegs();
  usb.options.hangStatus = true;
  const originalTimer = globalThis.setTimeout;
  globalThis.setTimeout = (fn, ms, ...args) => originalTimer(fn, ms >= 15000 ? 1 : ms, ...args);
  try { await assert.rejects(flashSealegs(s, image()), /timed out/); }
  finally { globalThis.setTimeout = originalTimer; }
  assert.equal(s.state, 'failed');
  assert.equal(mutations(usb).length, 0);
  await disconnectSealegs(s);
});

test('idle disconnect invalidates session and verified flag', async () => {
  const usb = fakeEnvironment();
  const s = await connectSealegs();
  assert.equal(s.usbDevice, usb);
  usb.manager.emit('disconnect', {device: usb});
  assert.equal(s.state, 'disconnected');
  await assert.rejects(flashSealegs(s, image()), /not ready/);
  assert.equal(mutations(usb).length, 0);
  await disconnectSealegs(s);
});

test('concurrent flash/restart/disconnect are refused while active', async () => {
  const usb = fakeEnvironment();
  const s = await connectSealegs();
  const task = flashSealegs(s, image());
  await assert.rejects(flashSealegs(s, image()), /not ready/);
  await assert.rejects(restartSealegs(s), /verified/);
  await assert.rejects(disconnectSealegs(s), /active USB/);
  await task;
  await disconnectSealegs(s);
});

test('image is copied before async operations and logging errors cannot abort writes', async () => {
  const usb = fakeEnvironment();
  const s = await connectSealegs();
  const data = image(), original = data.slice(0);
  const task = flashSealegs(s, data, () => { throw new Error('UI error'); }, () => { throw new Error('UI error'); });
  new Uint8Array(data).fill(0);
  await task;
  assert.deepEqual(usb.memory.slice(0, LENGTH), new Uint8Array(original));
  await disconnectSealegs(s);
});

for (const disconnect of [false, true]) {
  test(`restart ${disconnect ? 'accepts observed disconnect' : 'does not swallow unexplained USB errors'}`, async () => {
    const usb = fakeEnvironment();
    const s = await connectSealegs();
    await flashSealegs(s, image());
    usb.options[disconnect ? 'restartDisconnect' : 'restartError'] = true;
    if (disconnect) {
      assert.deepEqual(await restartSealegs(s), {restartRequested: true, disconnected: true});
    } else {
      await assert.rejects(restartSealegs(s), /Unexplained/);
      assert.equal(s.state, 'failed');
    }
    await disconnectSealegs(s);
  });
}
