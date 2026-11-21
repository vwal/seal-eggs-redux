import {OUTPUT_NAME, patchFor, identify, readFirmware, patchRedux} from './firmware-patch.js';
import {connectSealegs, flashSealegs, restartSealegs, disconnectSealegs} from './transport.js';

const message = error => error instanceof Error ? error.message : String(error);

function announce(element, text, state = '') {
  element.textContent = text;
  element.dataset.state = state;
}

class ReduxPatcher extends HTMLElement {
  connectedCallback() {
    if (this.childElementCount) return;
    this.innerHTML = `
      <label class="tool-file">Firmware to patch (.bin)
        <input type="file" accept=".bin,application/octet-stream" aria-describedby="patch-feedback">
      </label>
      <p class="tool-status" id="patch-feedback" role="status" aria-live="polite">Choose the official Sealegs.1.3.5.0.bin. Your file stays in this browser.</p>
      <p class="tool-help" data-guide hidden>Get the original Sealegs 1.3.5.0 file from <a href="https://intellijel.github.io/firmware/" target="_blank" rel="noopener noreferrer">Intellijel</a>. The full Seal Eggs build is also supported, with or without Tape Bright.</p>
      <div class="tool-actions">
        <button type="button" class="button" data-build disabled>Build Redux firmware</button>
        <a class="button" data-download download="Sealegs.1.3.5.0+c.bin" hidden>Download patched .bin</a>
      </div>`;
    const input = this.querySelector('input');
    const feedback = this.querySelector('[role=status]');
    const guide = this.querySelector('[data-guide]');
    const build = this.querySelector('[data-build]');
    const download = this.querySelector('[data-download]');
    let selection = 0;
    let source;
    let pending = false;
    const clearOutput = () => {
      if (download.hasAttribute('href')) URL.revokeObjectURL(download.href);
      download.removeAttribute('href');
      download.hidden = true;
    };
    input.addEventListener('change', async () => {
      const sequence = ++selection;
      clearOutput();
      build.disabled = true;
      source = null;
      guide.hidden = true;
      const file = input.files[0];
      if (!file) {
        announce(feedback, 'Choose the official Sealegs 1.3.5.0 .bin to begin.');
        return;
      }
      announce(feedback, 'Checking the firmware identity…');
      try {
        const checked = await readFirmware(file);
        if (sequence !== selection) return;
        if (checked.id === 'redux') {
          announce(feedback, 'This file already matches Redux 1.3.5.0+c. Choose it in the flasher below.', 'good');
        } else {
          source = checked;
          announce(feedback, `${checked.name} verified. Ready to build.`, 'good');
          build.disabled = false;
        }
      } catch (error) {
        if (sequence !== selection) return;
        guide.hidden = false;
        announce(feedback, message(error), 'bad');
      }
    });
    build.addEventListener('click', async () => {
      if (!source || pending) return;
      const sequence = selection;
      pending = true;
      input.disabled = true;
      build.disabled = true;
      clearOutput();
      announce(feedback, 'Applying the Redux patch and checking the result…');
      try {
        const url = new URL(patchFor(source.id).file, import.meta.url);
        const response = await fetch(url, {credentials: 'omit', referrerPolicy: 'no-referrer'});
        if (!response.ok) throw new Error('The Redux patch could not be loaded. Reload the page and try again.');
        const patched = await patchRedux(source.buffer, await response.arrayBuffer());
        if (sequence !== selection) return;
        download.href = URL.createObjectURL(new Blob([patched], {type: 'application/octet-stream'}));
        download.download = OUTPUT_NAME;
        download.hidden = false;
        announce(feedback, 'Redux 1.3.5.0+c verified. Save the file, then choose it in the flasher.', 'good');
      } catch (error) {
        if (sequence === selection) announce(feedback, message(error), 'bad');
      } finally {
        pending = false;
        input.disabled = false;
        build.disabled = !source || !download.hidden;
      }
    });
  }
}

class ReduxFlasher extends HTMLElement {
  connectedCallback() {
    if (this.childElementCount) return;
    this.innerHTML = `
      <label class="tool-file">Firmware to install (.bin)
        <input type="file" data-file accept=".bin,application/octet-stream" aria-describedby="flash-file-status">
      </label>
      <p class="tool-status" id="flash-file-status" role="status" aria-live="polite">Choose your downloaded Redux file, or official Sealegs 1.3.5.0 for a stock restore.</p>
      <label class="tool-check"><input type="checkbox" data-confirm> I have connected the rear USB port of my Sealegs and powered on while holding its rear BOOT button.</label>
      <div class="tool-actions">
        <button type="button" class="button" data-connect disabled>Connect Sealegs</button>
        <button type="button" class="button" data-flash disabled>Flash firmware</button>
        <button type="button" class="button" data-start hidden>Restart module</button>
        <button type="button" class="button secondary" data-disconnect hidden>Disconnect</button>
      </div>
      <p class="tool-status" data-status role="status" aria-live="polite">USB disconnected.</p>
      <progress data-progress max="100" value="0" aria-label="Firmware update progress" hidden></progress>
      <details class="tool-log"><summary>USB activity</summary><pre aria-label="USB activity log"></pre></details>`;
    const find = key => this.querySelector(`[data-${key}]`);
    const input = find('file');
    const confirm = find('confirm');
    const connect = find('connect');
    const flash = find('flash');
    const restart = find('start');
    const disconnect = find('disconnect');
    const feedback = find('status');
    const fileFeedback = this.querySelector('#flash-file-status');
    const progress = find('progress');
    const logText = this.querySelector('pre');
    const supported = window.isSecureContext && !!navigator.usb;
    let session;
    let image;
    let written;
    let busy = false;
    let sequence = 0;
    const log = entry => {
      logText.textContent += `${entry}\n`;
      logText.scrollTop = logText.scrollHeight;
    };
    const controls = () => {
      input.disabled = busy || !!written;
      confirm.disabled = busy || !!session;
      connect.disabled = busy || !!session || !confirm.checked || !image || !supported;
      flash.disabled = busy || !session || session.state !== 'connected' || !confirm.checked || !image || !!written;
      flash.textContent = image?.id === 'stock' ? 'Restore stock firmware' : 'Flash Redux firmware';
      restart.hidden = !written;
      restart.disabled = busy;
      disconnect.hidden = !session;
      disconnect.disabled = busy;
    };
    const close = async () => {
      const current = session;
      session = null;
      written = null;
      confirm.checked = false;
      if (current) {
        try { await disconnectSealegs(current); }
        catch (error) { log(message(error)); }
      }
    };
    input.addEventListener('change', async () => {
      const token = ++sequence;
      image = null;
      controls();
      if (!input.files[0]) {
        announce(fileFeedback, 'Choose a Redux or official stock .bin.');
        return;
      }
      announce(fileFeedback, 'Checking the selected file…');
      try {
        const selected = await readFirmware(input.files[0]);
        if (token !== sequence) return;
        if (!['redux', 'stock'].includes(selected.id)) throw new Error('This is a Seal Eggs base. Build Redux above and choose the downloaded result here.');
        image = selected;
        announce(fileFeedback, `${image.name} verified for ${image.id === 'stock' ? 'stock restore' : 'installation'}.`, 'good');
      } catch (error) { if (token === sequence) announce(fileFeedback, message(error), 'bad'); }
      controls();
    });
    confirm.addEventListener('change', controls);
    connect.addEventListener('click', async () => {
      if (connect.disabled) return;
      busy = true;
      controls();
      announce(feedback, 'Choose the STM32 bootloader in the USB device dialog.');
      try {
        session = await connectSealegs(log);
        if (session.state !== 'connected') throw new Error('The device disconnected. Re-enter bootloader mode and reconnect.');
        announce(feedback, 'Bootloader connected. Flashing will erase and replace the installed firmware.');
      } catch (error) {
        await close();
        announce(feedback, error.name === 'NotFoundError' ? 'Device selection cancelled.' : message(error), 'bad');
      } finally { busy = false; controls(); }
    });
    flash.addEventListener('click', async () => {
      if (flash.disabled) return;
      const selected = image;
      const current = session;
      busy = true;
      controls();
      progress.hidden = false;
      progress.value = 0;
      let wakeLock;
      try {
        const checked = await identify(selected.buffer);
        if (checked.id !== selected.id || !['stock', 'redux'].includes(checked.id)) throw new Error('Firmware identity changed before flashing.');
        try { wakeLock = await navigator.wakeLock?.request('screen'); } catch { /* Optional. */ }
        const labels = {erase: 'Erasing', write: 'Writing', verify: 'Verifying'};
        const ranges = {erase: [0, 10], write: [10, 55], verify: [65, 35]};
        let lastDisplay = '';
        await flashSealegs(current, checked.buffer, ({phase, done, total}) => {
          const fraction = total ? done / total : 0;
          const [offset, span] = ranges[phase];
          progress.value = offset + span * fraction;
          const display = `${labels[phase]} · ${Math.round(fraction * 100)}%`;
          if (display !== lastDisplay) announce(feedback, display);
          lastDisplay = display;
        }, log);
        written = selected;
        announce(feedback, `${selected.name} written and verified byte for byte. Restart the module to finish.`, 'good');
      } catch (error) {
        await close();
        announce(feedback, `Update stopped. ${message(error)} Power off and re-enter bootloader mode before retrying.`, 'bad');
      } finally {
        try { await wakeLock?.release(); } catch { /* Optional. */ }
        busy = false;
        controls();
      }
    });
    restart.addEventListener('click', async () => {
      if (busy || !written || session?.state !== 'verified') return;
      busy = true;
      controls();
      try {
        await restartSealegs(session, log);
        announce(feedback, 'Restart requested. Power off, disconnect USB, then power on normally.', 'good');
      } catch (error) {
        announce(feedback, `Firmware was verified. ${message(error)} Power off, disconnect USB and power on normally.`);
      } finally {
        await close();
        busy = false;
        controls();
      }
    });
    disconnect.addEventListener('click', async () => {
      if (busy || !session) return;
      busy = true;
      controls();
      await close();
      busy = false;
      controls();
      announce(feedback, 'USB disconnected.');
    });
    navigator.usb?.addEventListener('disconnect', async event => {
      if (busy || !session || session.usbDevice !== event.device) return;
      await close();
      announce(feedback, 'USB disconnected. Re-enter bootloader mode and reconnect before updating.');
      controls();
    });
    window.addEventListener('beforeunload', event => {
      if (!busy) return;
      event.preventDefault();
      event.returnValue = '';
    });
    if (!supported) announce(feedback, 'USB flashing requires desktop Chrome or Edge over HTTPS. You can still build and download the patch here.');
    controls();
  }
}

customElements.define('redux-patcher', ReduxPatcher);
customElements.define('redux-flasher', ReduxFlasher);
