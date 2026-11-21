/* Conservative Sealegs adapter for the unmodified Intellijel/WebDFU vendors.
 * Protocol: ST AN3156 Rev 19. No device operations run at module load.
 * A matching STM32 VID/PID identifies a bootloader, NOT the Sealegs product.
 */
const BASE = 0x08000000;
const LENGTH = 589964;
const END = BASE + LENGTH;
const VID = 0x0483, PID = 0xdf11;
const IO_MS = 15000, COMMAND_MS = 120000, FLASH_MS = 600000;
const sessions = new WeakMap();
const hex = n => `0x${n.toString(16).padStart(8, '0')}`;
const fail = message => { throw new Error(message); };
const emit = (callback, value) => { try { callback?.(value); } catch (_) { /* UI cannot interrupt USB. */ } };
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

function stateOf(session) {
  const s = sessions.get(session);
  if (!s) fail('Unknown session. Connect the module first.');
  return s;
}

function setState(s, state) { s.state = state; }

async function bounded(s, label, action, timeout = IO_MS) {
  if (s.timedOut) fail('The USB session timed out. Disconnect and re-enter bootloader mode.');
  const ms = Math.min(timeout, s.deadline - Date.now());
  if (ms <= 0) { s.timedOut = true; fail(`${label}: operation deadline exceeded.`); }
  let timer;
  try {
    return await Promise.race([
      Promise.resolve().then(action),
      new Promise((_, reject) => { timer = setTimeout(() => {
        s.timedOut = true;
        reject(new Error(`${label}: timed out. No further USB commands will be sent by this session.`));
      }, ms); }),
    ]);
  } finally { clearTimeout(timer); }
}

async function input(s, setup, length) {
  const result = await bounded(s, 'USB read', () => s.usb.controlTransferIn(setup, length));
  if (result.status !== 'ok' || !(result.data instanceof DataView) || result.data.byteLength !== length) {
    fail(`USB read failed or was short (${result.status}, expected ${length} bytes).`);
  }
  return result.data;
}

async function output(s, setup, data = new ArrayBuffer(0)) {
  const result = await bounded(s, 'USB write', () => s.usb.controlTransferOut(setup, data));
  if (result.status !== 'ok' || result.bytesWritten !== data.byteLength) {
    fail(`USB write failed or was short (${result.status}, expected ${data.byteLength} bytes).`);
  }
  return result.bytesWritten;
}

async function descriptor(s, type, index, language = 0) {
  const setup = {requestType: 'standard', recipient: 'device', request: 6,
    value: (type << 8) | index, index: language};
  const header = await input(s, setup, type === 2 ? 4 : 2);
  const length = type === 2 ? header.getUint16(2, true) : header.getUint8(0);
  if (header.getUint8(1) !== type || length < (type === 2 ? 9 : 2) || length > 65535) {
    fail('Malformed USB descriptor.');
  }
  const data = await input(s, setup, length);
  if (data.getUint8(1) !== type || (type === 2 ? data.getUint16(2, true) : data.getUint8(0)) !== length) {
    fail('USB descriptor changed while being read.');
  }
  return data;
}

function parseConfig(data) {
  if (data.getUint8(0) !== 9) fail('Unsupported configuration descriptor header.');
  const records = [], functional = new Map();
  let current = null;
  for (let offset = 9; offset < data.byteLength;) {
    if (offset + 2 > data.byteLength) fail('Truncated USB descriptor.');
    const size = data.getUint8(offset), type = data.getUint8(offset + 1);
    if (size < 2 || offset + size > data.byteLength) fail('Malformed USB subdescriptor length.');
    if (type === 4) {
      if (size !== 9) fail('Malformed interface descriptor.');
      current = {number: data.getUint8(offset + 2), alt: data.getUint8(offset + 3),
        class: data.getUint8(offset + 5), subclass: data.getUint8(offset + 6),
        protocol: data.getUint8(offset + 7), string: data.getUint8(offset + 8)};
      records.push(current);
    } else if (type === 0x21 && current?.class === 0xfe && current.subclass === 1) {
      if (size !== 9) fail('Malformed DFU functional descriptor.');
      const list = functional.get(current.number) || [];
      list.push({attributes: data.getUint8(offset + 2), transferSize: data.getUint16(offset + 5, true),
        version: data.getUint16(offset + 7, true)});
      functional.set(current.number, list);
    }
    offset += size;
  }
  return {value: data.getUint8(5), records, functional};
}

async function stringDescriptor(s, index) {
  if (!index) fail('The flash alternate has no memory map name.');
  const languages = await descriptor(s, 3, 0);
  if (languages.byteLength < 4 || languages.byteLength % 2) fail('Malformed USB language descriptor.');
  let language = languages.getUint16(2, true);
  for (let i = 2; i < languages.byteLength; i += 2) {
    if (languages.getUint16(i, true) === 0x0409) language = 0x0409;
  }
  const data = await descriptor(s, 3, index, language);
  if (data.byteLength % 2) fail('Malformed USB string descriptor.');
  let text = '';
  for (let i = 2; i < data.byteLength; i += 2) text += String.fromCharCode(data.getUint16(i, true));
  return text;
}

function flashPlan(name) {
  // The upstream parser ignores unmatched text. Validate the entire string first.
  const prefix = /^@Internal\s+Flash\s*/i.exec(name);
  const mapSyntax = /^(?:\/\s*0x[0-9a-fA-F]{1,8}\s*\/(?:\s*\d+\s*\*\s*\d+\s?[ BKM]\s*[abcdefg]\s*)(?:,\s*\d+\s*\*\s*\d+\s?[ BKM]\s*[abcdefg]\s*)*)+$/;
  if (!prefix || !mapSyntax.test(name.slice(prefix[0].length))) fail('Unrecognized or incomplete internal flash memory map.');
  const info = globalThis.dfuse.parseMemoryDescriptor(name);
  const segments = info.segments.slice().sort((a, b) => a.start - b.start);
  if (!segments.length || segments[0].start !== BASE) fail('Internal flash does not start at 0x08000000.');
  let previousEnd = 0;
  for (const g of segments) {
    if (![g.start, g.end, g.sectorSize].every(Number.isSafeInteger) || g.start < previousEnd ||
        g.end <= g.start || g.end > 0x100000000 || g.sectorSize <= 0 ||
        (g.end - g.start) % g.sectorSize !== 0) fail('Invalid or overlapping flash sectors.');
    previousEnd = g.end;
  }
  const sectors = [];
  let address = BASE;
  while (address < END) {
    const g = segments.find(segment => segment.start <= address && address < segment.end);
    if (!g || !g.readable || !g.erasable || !g.writable) fail(`Flash at ${hex(address)} is not readable, erasable and writable.`);
    if ((address - g.start) % g.sectorSize) fail('Firmware starts partway through an erase sector.');
    sectors.push({start: address, size: g.sectorSize});
    if (sectors.length > 8192) fail('Unsupported number of erase sectors.');
    address += g.sectorSize;
  }
  // Each sector intersects the image. There is no mass erase or extra-sector erase.
  return {sectors, eraseEnd: address};
}

function installStrictRequests(s) {
  s.device.requestIn = (request, length, value = 0) => input(s, {
    requestType: 'class', recipient: 'interface', request, value, index: s.device.intfNumber,
  }, length);
  s.device.requestOut = (request, data, value = 0) => output(s, {
    requestType: 'class', recipient: 'interface', request, value, index: s.device.intfNumber,
  }, data);
}

async function status(s) {
  const d = await s.device.requestIn(globalThis.dfu.GETSTATUS, 6);
  const result = {status: d.getUint8(0), state: d.getUint8(4),
    pollTimeout: d.getUint8(1) | (d.getUint8(2) << 8) | (d.getUint8(3) << 16)};
  if (result.status !== 0 || result.state === globalThis.dfu.dfuERROR) {
    fail(`DFU reported error status ${result.status}, state ${result.state}. Re-enter bootloader mode before trying again.`);
  }
  s.protocolState = result.state;
  return result;
}

async function pollDownload(s) {
  const deadline = Math.min(s.deadline, Date.now() + COMMAND_MS);
  for (;;) {
    const result = await status(s);
    if (result.state === globalThis.dfu.dfuDNLOAD_IDLE) return;
    if (![globalThis.dfu.dfuDNLOAD_SYNC, globalThis.dfu.dfuDNBUSY].includes(result.state)) {
      fail(`Unexpected DFU state ${result.state} during download.`);
    }
    const pause = Math.max(1, result.pollTimeout);
    if (Date.now() + pause >= deadline) fail('DFU command exceeded its polling deadline.');
    await delay(pause);
  }
}

async function command(s, code, address) {
  const bytes = new ArrayBuffer(5), view = new DataView(bytes);
  view.setUint8(0, code);
  view.setUint32(1, address, true);
  await s.device.download(bytes, 0);
  await pollDownload(s);
}

async function abortToIdle(s) {
  await s.device.abort();
  if ((await status(s)).state !== globalThis.dfu.dfuIDLE) fail('DFU did not return to idle after ABORT.');
}

export async function connectSealegs(onLog) {
  if (!globalThis.dfu || !globalThis.dfuse) fail('Official DFU libraries have not loaded.');
  if (globalThis.isSecureContext === false || !globalThis.navigator?.usb) {
    fail('WebUSB requires a supported browser on localhost or HTTPS.');
  }
  // The browser chooser is deliberately outside a timer: it is a user decision.
  const usb = await navigator.usb.requestDevice({filters: [{vendorId: VID, productId: PID}]});
  if (usb.vendorId !== VID || usb.productId !== PID) fail('Select an STM32 ROM DFU device (0483:df11).');
  const s = {usb, deadline: Date.now() + 60000, timedOut: false, state: 'connecting', busy: false,
    verified: false, protocolState: null};
  try {
    await bounded(s, 'Opening USB device', () => usb.open());
    const interfaces = globalThis.dfu.findDeviceDfuInterfaces(usb).filter(i => i.alternate.interfaceProtocol === 2);
    if (!interfaces.length) fail('The device is not in ROM DFU mode.');
    const configs = new Map();
    for (let i = 0; i < usb.configurations.length; i++) {
      const conf = parseConfig(await descriptor(s, 2, i));
      if (conf.value !== usb.configurations[i].configurationValue || configs.has(conf.value)) fail('Inconsistent USB configuration descriptors.');
      configs.set(conf.value, conf);
    }
    const candidates = [];
    for (const settings of interfaces) {
      const conf = configs.get(settings.configuration.configurationValue);
      const records = conf.records.filter(r => r.number === settings.interface.interfaceNumber && r.alt === settings.alternate.alternateSetting);
      if (records.length !== 1 || records[0].class !== 0xfe || records[0].subclass !== 1 || records[0].protocol !== 2) {
        fail('Inconsistent USB interface descriptors.');
      }
      const name = settings.name || await stringDescriptor(s, records[0].string);
      if (/^@Internal\s+Flash\b/i.test(name)) {
        const plan = flashPlan(name);
        const descriptors = conf.functional.get(settings.interface.interfaceNumber) || [];
        if (descriptors.length !== 1) fail('DFU functional descriptor is missing or ambiguous.');
        const props = descriptors[0];
        if (props.version !== 0x011a || (props.attributes & 3) !== 3) fail('DfuSe 1.1a with upload and download support is required.');
        if (!Number.isInteger(props.transferSize) || props.transferSize < 2 || props.transferSize > 2048 || props.transferSize % 4) {
          fail('Unsupported DfuSe transfer size (must be a multiple of four, up to 2048 bytes).');
        }
        candidates.push({settings: {...settings, name}, props, plan});
      }
    }
    if (candidates.length !== 1) fail('An unambiguous internal flash alternate at 0x08000000 is required.');
    const {settings, props, plan} = candidates[0];
    if (usb.configuration?.configurationValue !== settings.configuration.configurationValue) {
      await bounded(s, 'Selecting USB configuration', () => usb.selectConfiguration(settings.configuration.configurationValue));
    }
    const intfNumber = settings.interface.interfaceNumber;
    const intf = usb.configuration.interfaces.find(i => i.interfaceNumber === intfNumber);
    if (!intf) fail('Selected USB interface disappeared.');
    if (!intf.claimed) await bounded(s, 'Claiming DFU interface', () => usb.claimInterface(intfNumber));
    if (intf.alternate?.alternateSetting !== settings.alternate.alternateSetting) {
      await bounded(s, 'Selecting internal flash', () => usb.selectAlternateInterface(intfNumber, settings.alternate.alternateSetting));
    }
    s.device = new globalThis.dfuse.Device(usb, settings);
    s.device.startAddress = BASE;
    s.transferSize = props.transferSize;
    s.plan = plan;
    installStrictRequests(s);
    if ((await status(s)).state !== globalThis.dfu.dfuIDLE) fail('DFU is not idle. Power off and re-enter bootloader mode.');
    s.disconnectListener = event => {
      if (event.device === usb && !s.busy && ['connected', 'verified'].includes(s.state)) {
        setState(s, 'disconnected');
        s.verified = false;
      }
    };
    navigator.usb.addEventListener('disconnect', s.disconnectListener);
    const session = Object.freeze({
      usbDevice: usb,
      productName: usb.productName || 'STM32 ROM bootloader', serialNumber: usb.serialNumber || '',
      vendorId: VID, productId: PID, configurationValue: settings.configuration.configurationValue,
      interfaceNumber: intfNumber, alternateSetting: settings.alternate.alternateSetting,
      transferSize: props.transferSize, flashStart: BASE, flashEnd: END,
      eraseEnd: plan.eraseEnd, sectorCount: plan.sectors.length,
      get state() { return s.state; }, get verified() { return s.verified; },
    });
    sessions.set(session, s);
    setState(s, 'connected');
    emit(onLog, `Connected to STM32 DFU; internal flash ${hex(BASE)}–${hex(END)}; ${plan.sectors.length} sectors through ${hex(plan.eraseEnd)}.`);
    emit(onLog, 'The ROM USB identity cannot distinguish Sealegs from another STM32 product.');
    return session;
  } catch (error) {
    // Closing a handle never sends erase/download/detach commands.
    try { await Promise.race([usb.close(), delay(2000)]); } catch (_) {}
    throw error;
  }
}

function validateImage(image) {
  if (!(image instanceof ArrayBuffer) || image.byteLength !== LENGTH) fail(`Firmware must be a raw ${LENGTH}-byte Sealegs image.`);
  const bytes = new Uint8Array(image.slice(0)); // Own the bytes despite later UI changes.
  const vectors = new DataView(bytes.buffer);
  if (vectors.getUint32(0, true) !== 0x20020000 || vectors.getUint32(4, true) !== 0x0802be39) {
    fail('Firmware vectors do not match the audited Sealegs 1.3.5.0 image.');
  }
  return bytes;
}

export async function flashSealegs(session, image, onProgress, onLog) {
  const s = stateOf(session);
  if (s.busy || !['connected', 'verified'].includes(s.state)) fail('This session is not ready to flash. Reconnect after any failure.');
  const bytes = validateImage(image); // No USB requests, including erase, before this passes.
  s.busy = true;
  s.verified = false;
  s.deadline = Date.now() + FLASH_MS;
  setState(s, 'flashing');
  try {
    if ((await status(s)).state !== globalThis.dfu.dfuIDLE) fail('DFU is no longer idle.');
    // Capability bits do not prove read access (for example, RDP may prohibit
    // it). Exercise the verification protocol before the first destructive
    // request. Existing contents/version are deliberately not interpreted.
    emit(onLog, 'Checking flash read access before erasing.');
    await command(s, globalThis.dfuse.SET_ADDRESS, BASE);
    await abortToIdle(s);
    await s.device.upload(8, 2);
    if ((await status(s)).state !== globalThis.dfu.dfuUPLOAD_IDLE) fail('Flash read access check did not reach upload idle.');
    await abortToIdle(s);
    emit(onLog, `Erasing ${s.plan.sectors.length} sectors; the unused tail through ${hex(s.plan.eraseEnd)} is erased too.`);
    emit(onProgress, {phase: 'erase', done: 0, total: s.plan.eraseEnd - BASE});
    for (const sector of s.plan.sectors) {
      await command(s, globalThis.dfuse.ERASE_SECTOR, sector.start);
      emit(onProgress, {phase: 'erase', done: sector.start + sector.size - BASE, total: s.plan.eraseEnd - BASE});
    }
    emit(onLog, 'Writing firmware.');
    emit(onProgress, {phase: 'write', done: 0, total: bytes.length});
    for (let offset = 0; offset < bytes.length; offset += s.transferSize) {
      const chunk = bytes.slice(offset, offset + s.transferSize);
      await command(s, globalThis.dfuse.SET_ADDRESS, BASE + offset);
      await s.device.download(chunk.buffer, 2);
      await pollDownload(s);
      emit(onProgress, {phase: 'write', done: offset + chunk.length, total: bytes.length});
    }
    emit(onLog, 'Reading flash back and comparing every byte before restart.');
    emit(onProgress, {phase: 'verify', done: 0, total: bytes.length});
    await abortToIdle(s);
    for (let offset = 0; offset < bytes.length; offset += s.transferSize) {
      const length = Math.min(s.transferSize, bytes.length - offset);
      await command(s, globalThis.dfuse.SET_ADDRESS, BASE + offset);
      await abortToIdle(s);
      // AN3156: address=(block-2)*CURRENT request length+pointer. Always use
      // block 2 and an explicit pointer, including the final 140-byte request.
      const data = await s.device.upload(length, 2);
      if ((await status(s)).state !== globalThis.dfu.dfuUPLOAD_IDLE) fail('Unexpected state after reading flash.');
      for (let i = 0; i < length; i++) {
        if (data.getUint8(i) !== bytes[offset + i]) fail(`Readback mismatch at ${hex(BASE + offset + i)}. Do not restart; re-enter bootloader mode and restore firmware.`);
      }
      await abortToIdle(s);
      emit(onProgress, {phase: 'verify', done: offset + length, total: bytes.length});
    }
    s.verified = true;
    setState(s, 'verified');
    emit(onLog, `All ${bytes.length} bytes match. The module remains in DFU mode until Restart is selected.`);
    return {bytesWritten: bytes.length, bytesVerified: bytes.length, eraseStart: BASE, eraseEnd: s.plan.eraseEnd};
  } catch (error) {
    setState(s, 'failed');
    emit(onLog, `Stopped: ${error?.message || error}. No retry or restart was sent.`);
    throw error;
  } finally { s.busy = false; }
}

export async function restartSealegs(session, onLog) {
  const s = stateOf(session);
  if (s.busy || s.state !== 'verified' || !s.verified) fail('Restart requires a completely verified write in this session.');
  s.busy = true;
  s.deadline = Date.now() + 15000;
  let disconnected = false, manifestationRequested = false;
  const listener = event => { if (event.device === s.usb && manifestationRequested) disconnected = true; };
  navigator.usb.addEventListener('disconnect', listener);
  try {
    if ((await status(s)).state !== globalThis.dfu.dfuIDLE) fail('DFU is no longer idle.');
    await command(s, globalThis.dfuse.SET_ADDRESS, BASE);
    await s.device.download(new ArrayBuffer(0), 0);
    manifestationRequested = true;
    try {
      for (;;) {
        const result = await status(s);
        if ([globalThis.dfu.dfuMANIFEST, globalThis.dfu.dfuMANIFEST_WAIT_RESET].includes(result.state)) break;
        if (result.state !== globalThis.dfu.dfuMANIFEST_SYNC) fail(`Unexpected restart state ${result.state}.`);
        const pause = Math.max(1, result.pollTimeout);
        if (Date.now() + pause >= s.deadline) fail('Restart confirmation timed out.');
        await delay(pause);
      }
    } catch (error) {
      if (!disconnected) throw error;
    }
    setState(s, 'restarted');
    emit(onLog, 'Restart requested. Confirm that the module starts normally; USB cannot verify application behavior.');
    return {restartRequested: true, disconnected};
  } catch (error) {
    setState(s, 'failed');
    throw error;
  } finally {
    navigator.usb.removeEventListener('disconnect', listener);
    s.busy = false;
  }
}

export async function disconnectSealegs(session) {
  const s = stateOf(session);
  if (s.busy) fail('Wait for the active USB operation to stop before disconnecting.');
  // The browser cannot cancel an outstanding timed-out control transfer. Close
  // the handle; never issue an ABORT, reset, detach, erase or retry here.
  let timer;
  try {
    await Promise.race([s.usb.close(), new Promise((_, reject) => {
      timer = setTimeout(() => reject(new Error('Closing USB timed out. Unplug and re-enter bootloader mode.')), 5000);
    })]);
  } finally {
    clearTimeout(timer);
    navigator.usb.removeEventListener('disconnect', s.disconnectListener);
    setState(s, 'closed');
    s.verified = false;
  }
}
