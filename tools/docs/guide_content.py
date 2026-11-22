"""Original release-guide text, organized by physical controls and playing mode."""

LED_COLORS = {"Blue": "#276CA5", "Amber": "#BC7622", "Orange": "#D56A26", "Cyan": "#1590A8",
              "Magenta": "#B5428D", "Green": "#388451", "Teal": "#00827C", "Yellow": "#AD8B13"}


def H(t):
    return "heading", t


def P(t):
    return "p", t


def N(t, s):
    return "note", (t, s)


def T(headers, widths, rows, compact=False):
    return ("compact" if compact else "table"), (headers, widths, rows)


def pairs(a, b, rows, frac=.275, compact=False):
    return T([a, b], [frac, 1 - frac], rows, compact)


def page(heading, sub, *blocks):
    return heading, sub, blocks


options = T(["MODEL", "FREEZE", "TAP", "DELAY SYNC"], [.115, .205, .31, .37], [
    ["TAPE", "{Blue} Noise<br/>{Amber} Character", "{Blue} Stock tone<br/>{Amber} Bright", "{Blue} Stock pickup<br/>{Amber} Fast pickup"],
    ["BBD", "{Blue} Noise<br/>{Amber} Character", "{Blue} Stock tone<br/>{Amber} Light", "Dark / unused"],
    ["DIGI", "{Blue} Noise<br/>{Amber} Character", "{Blue} Digital<br/>{Green} Cold Digital<br/>{Amber} Sunny Tape", "{Blue} Stock<br/>{Cyan} Smooth<br/>{Amber} Stepped<br/>{Magenta} Throw"],
], True)

open_options = N("Enter, edit, save", "Choose MODEL first. Hold MOD SYNC alone for about 1 second, then release. Tap an option button to cycle its choices. Tap MOD SYNC, hold it for about half a second, or change MODEL to save and exit. Wait for the brief green save flash after an edit.")

alt_engines = N("Enter or leave an alternate engine", "With BBD or DIGI selected, hold FREEZE/ALT + DELAY SYNC together for about 1 second. Release both. TAP breathes orange for Microloops or teal for Beads. Repeat the gesture or move MODEL away to leave.")

run_throw = N("Launch a Pitch Throw", "Set DIGI / DELAY SYNC to magenta in options, then exit. Let TIME/L rest for about 0.1 second. Move it at least 2% of its travel. Shorter TIME throws up, longer TIME throws down. One echo glides toward five semitones and fades over two seconds while the regular delay continues.")

recharge = N("Reposition TIME/L quietly", "In native Digi Smooth, Stepped or Throw, close options. Hold FREEZE/ALT for about half a second, move TIME/L, then release. The manual delay time stays put until the slider crosses its old position. In Throw you can re-arm at the new position before pickup. A voice already in flight finishes its bend.")

quality_pending = P("The DIGI TAP choice sets <b>Beads</b> recording quality. A blinking colour means it is pending. Leave and re-enter Beads to apply it. Entry starts a fresh recording.")

credit = P("<b>Credits</b>  Intellijel designed Sealegs and its stock firmware. BRIBERY created Seal Eggs, including live reverse, Character, Stepped Doppler, Tape and BBD options, Seal Beads and Seal Microloops. Seal Beads uses Beads and stmlib code by Émilie Gillet. The Redux project added the settings layer, Smooth, Throw, quiet pickup and the two additional Beads media.")

credit_short = P("<b>Origins</b>  Intellijel designed Sealegs. BRIBERY created Seal Eggs, its native enhancements and both alternate engines. Seal Beads incorporates Beads and stmlib by Émilie Gillet. Redux adds the saved options, Smooth, Throw, quiet pickup and two Beads qualities.")

start_micro = N("A clocked starting patch", "Play a drum loop. Send a short trigger per quarter note at 120 BPM, enable DELAY SYNC and turn triplets off. Begin with MIX wet, DRIVE at noon, MOD at 70%, WIDTH 15%, COLOR centred, FB/NOISE/FOG down, HP down and LP up. Give the buffer two bars to capture audio.")

alt_summary = T(["Control", "BBD · Microloops", "DIGI · Beads"], [.23, .38, .39], [
    ["TIME RANGE", "Short Drone / Med Shuffle / Long Octaves", "Short, Med and Long increase the available look-back window."],
    ["TIME/L · WIDTH/R", "Loop or step duration / number of repeats before capture", "Look-back through the recording / grain length"],
    ["MOD RATE · DEPTH", "Variation A to D / strength or layers", "Grain pitch / density of grain starts"],
    ["MOD · COLOR", "Overlap / loop-edge shape", "Overlap / grain envelope"],
    ["NOISE · FEEDBACK", "Scatter or rearrange / record loops back in", "Spray grain position / return grains to buffer"],
    ["DELAY · MOD SYNC", "Lock loop and step timing / triplets", "Lock grain timing / triplets"],
], True)

native_buttons = pairs("Gesture", "During ordinary Tape, BBD or Digi delay", [
    ["Tap FREEZE", "Toggles live reverse at power-up. With the alternate assignment, it toggles native Freeze."],
    ["ALT + TAP", "Short press cycles AUX CV destination on release. Hold both about 1 second to swap the FREEZE tap assignment between Reverse and Freeze."],
    ["TAP twice or more", "With a SYNC active and CLK IN empty, sets tempo. With MOD SYNC on, TAP resets the LFO now on tap tempo or at the next external pulse."],
    ["Tap DELAY SYNC", "Toggles delay clocking (orange when on). Hold DELAY SYNC alone over 1 second to clear recorded delay audio."],
    ["Tap MOD SYNC", "Toggles modulation clocking for oscillating waves. Orange means synced. Hold alone about 1 second to enter Redux options."],
    ["ALT + DELAY SYNC", "A short press toggles cross-feedback. A long hold enters the alternate engine on BBD or DIGI."],
    ["ALT + MOD SYNC", "A short press inverts right-channel internal modulation. Hold about 1 second to switch NOISE / Character for this native model."],
], .245, True)

global_rows = [
    ["DRIVE", "Input level / drive. Noon gives unity before further gain and saturation.", "Input trim from 0.5× to 2.5×, unity at noon. Set loud peaks just below the trim indicator."],
    ["NOISE", "Native noise level or model Character when selected. In an alternate engine, scatter or spray.", "Native noise texture sweeps from pre-delay hiss through crackle to post-delay hiss."],
    ["FOG", "Reverb amount.", "Set reverb decay."],
    ["MOD", "Native modulation waveform. Alternate engines use this knob for overlap.", "On a native delay, jump directly between named waveforms."],
    ["FOG / DRIVE switch", "Choose reverb position. IN before delay, DLY on the wet path, MIX after wet/dry.", "Choose and save drive position. Move away and back to select the already occupied position."],
    ["MIX", "Dry to wet. In Send/Return mode this sets the wet output level.", "—"],
]

q1 = page("Buttons and model options", "ALT means hold FREEZE. To install Redux, patch official 1.3.5.0 on the <link href='https://vwal.github.io/seal-eggs-redux/' color='#165F56'><u>release site</u></link>, then flash the saved +c file.",
          H("Native buttons and shortcuts"), native_buttons, H("Options for the current model"), open_options, options,
          P("MOD SYNC breathes white in options, alternating with teal for active Beads or orange for active Microloops. Knobs, sliders and CV keep playing. TAP's ordinary tempo pulse is hidden here."))

q2 = page("The native delay", "These mappings apply during ordinary Tape, BBD and Digi playback. Inside Beads and Microloops the same sliders take new roles.",
          H("TIME RANGE and synced timing"), T(["Switch", "Free TIME", "Interval in incoming clock pulses, slider bottom to top"], [.14, .21, .65], [
              ["SHORT", "3.125-93.75 ms", "1/4 · 1/3 · 3/8 · 1/2 · 2/3 · 3/4 · 1"],
              ["MED", "50 ms-1.5 s", "1 · 1 1/3 · 1 1/2 · 2 · 2 2/3 · 3 · 4"],
              ["LONG", "200 ms-6 s", "4 · 5 1/3 · 6 · 8 · 10 2/3 · 12 · 16"],
          ], True), P("TIME/L increases as the slider rises. DELAY SYNC uses CLK IN or tapped tempo. For a sixteenth-note clock, the MED range runs from a sixteenth note to a quarter note."),
          H("STEREO CONFIG and feedback"), pairs("Switch", "Delay routing", [
              ["PONG", "Sums the inputs, then runs the two delays in series. WIDTH/R adds up to 33% to the second delay. Cross-feedback reverses their order."],
              ["T:W", "Parallel stereo. TIME/L sets the base time. WIDTH/R offsets the right delay by up to 33%."],
              ["L/R", "Parallel stereo. TIME/L sets left delay time, WIDTH/R sets right delay time. Cross-feedback exchanges repeats between sides in either parallel mode."],
              ["FEEDBACK", "Returns delayed sound to the input. Above 100% echoes can grow into oscillation. The slider reaches 160%."],
          ], .205, True), H("MODEL, COLOR and native Freeze"), T(["Model", "COLOR as it rises", "With native Freeze engaged"], [.145,.34,.515], [
              ["TAPE", "Drag, wear and dropouts", "Input closes and feedback holds. Time and modulation still act. The held sound gradually saturates."],
              ["BBD", "Companding noise and clock instability", "The recirculating signal gradually loses highs and level, especially at long times."],
              ["DIGI", "Bit-depth / sample-rate reduction", "The recorded buffer holds indefinitely. TIME and modulation leave the frozen contents intact."],
          ], True),
          P("HP FREQ and LP FREQ shape the repeats at 6 dB/octave. Open them with HP down and LP up. In native Freeze they filter the output. Character on NOISE adds a second model-specific control alongside COLOR."))

q3 = page("Modulation, routing and I/O", "The same panel sets signal level, reverb placement and external modulation. ALT reveals the secondary controls.",
          H("Knobs and placement"), T(["Control", "During play", "While holding ALT"],[.19,.395,.415],global_rows,True),
          H("Native modulation"), pairs("Control", "Response", [
              ["MOD waveform", "Clockwise order is Wow & Flutter, inverted follower, follower, LFV, sample & hold, square, sine, saw, triangle, ramp. The first three are discrete. From LFV onward, adjacent shapes blend."],
              ["RATE / DEPTH", "Free RATE covers 0.1-40 Hz. Synced cycle lengths in pulses are 64, 32, 16, 8, 4, 2, 1, 1/2, 1/4. Followers and Wow & Flutter ignore sync. DEPTH sets internal delay-time modulation."],
              ["MOD OUT", "Full modulation signal regardless of DEPTH. Positive lights the upper green LED, negative lights the lower red LED. Brightness follows amplitude."],
          ], .235, True),
          H("Jacks and AUX assignment"), pairs("Jack or control", "Use", [
              ["Audio IN / OUT", "Patch mono into L. The left input feeds the right input when R is empty. OUT L/R carry the stereo result."],
              ["FREEZE / CLK", "High gate engages native Freeze and low releases it. CLK supplies timing for sync."],
              ["CV attenuverters", "TIME/L, WIDTH/R, FB, MOD RATE, MOD DEPTH, COLOR, HP and LP each have CV. Noon cancels CV. Clockwise adds it and counterclockwise inverts it."],
              ["AUX + ALT/TAP", "Cycle on TAP release. Flash count / destination are 1 magenta DRIVE, 2 yellow NOISE, 3 white MOD wave, 4 green FOG, 5 blue MIX. AUX has its own attenuverter."],
          ], .235, True))

q4 = page("Alternate engines and startup", "Use this side for alternate-engine controls, Digi pitch gestures and the settings reached only during power-on.",
          alt_engines, alt_summary,
          N("Smooth, Stepped and Throw", "Choose the native Digi response with DELAY SYNC in options. Cyan bends continuously. Amber uses semitone steps on large moves. Magenta launches a two-second echo over the normal delay. Shorten TIME for a rising throw, lengthen it for a falling throw."),
          recharge, quality_pending, H("Hold a single button while powering on"),
          pairs("Button", "What the LEDs confirm", [
              ["DELAY SYNC", "Toggle Send/Return. Red means enabled with wet-only level control on MIX. Green means ordinary dry/wet."],
              ["MOD SYNC", "Toggle the global drive tone. Blue selects the darker voicing. Cyan selects the brighter 1.3 voicing. Tape Bright in Redux options is a separate Tape tone choice."],
              ["FREEZE", "Yellow confirms a factory reset. This restores saved settings, including the Redux defaults."],
          ], .23, True),
          P("Normal startup displays four numeric digits on FREEZE / TAP / DELAY SYNC / MOD SYNC for about three seconds. Colours 0-9 are blue, cyan, green, yellow, orange, red, magenta, purple, grey and white. The community release label is 1.3.5.0+c."), credit_short)

n1 = page("Release controls at a glance", "Patch official 1.3.5.0 on the <link href='https://vwal.github.io/seal-eggs-redux/' color='#165F56'><u>Redux site</u></link> and flash the saved +c file. This side covers Tape, BBD and Digi. Turn over for the alternate engines.",
          open_options, options, H("What each native option changes"),
          pairs("Selection", "Sound or gesture", [
              ["Character · all models", "The NOISE knob becomes tape grunge, BBD chip decay or Digi data corruption. Each model saves its own assignment. The ALT + MOD SYNC long shortcut still works in normal play."],
              ["Tape · Bright / Fast", "Bright opens the high end. Fast makes Tape follow TIME moves about five times faster. Set each independently."],
              ["BBD · Light", "Raises the BBD filter ceiling from 4.2 to 12 kHz. The LP slider still darkens the repeats."],
              ["Digi · Stock / Smooth / Stepped", "Stock crossfades between delay times. Smooth bends continuously as TIME changes. Stepped is the Seal Eggs response with semitone steps on bigger moves."],
              ["Live reverse", "Tap FREEZE to reverse slices while input and feedback continue. Hold ALT + TAP about 1 second to assign the tap to native Freeze. Each boot starts forward with the tap assigned to Reverse."],
          ], .27, True), run_throw, recharge)

n2 = page("The two alternate engines", "BRIBERY's Seal Beads V2 and Seal Microloops share the panel. Redux adds recording quality selection in Beads.",
          alt_engines, alt_summary, H("Microloops variations"),
          T(["TIME RANGE", "RATE A", "RATE B", "RATE C", "RATE D"], [.18,.205,.205,.205,.205], [
              ["SHORT · Drone", "Breathing loop", "Low octave + moving low-pass", "Resonant note per capture", "Loud hits shorten the loop"],
              ["MED · Shuffle", "Step-by-step low-pass", "Half-speed steps, pad above 90% DEPTH", "Overlapping resonant sweeps", "Double-time and crushed bass"],
              ["LONG · Octaves", "Normal and up", "Normal and down", "All voices up", "Half, normal, double and quadruple speed"],
          ], True), P("RATE chooses A/B/C/D from bottom to top. Start inside a zone at about 12%, 38%, 62% or 88%. DEPTH introduces activity or additional layers. For predictable synced playback, use short CLK triggers."),
          H("Beads quality and active-engine gestures"), quality_pending,
          P("<b>Digital</b> uses the original Seal Beads medium. <b>Cold</b> uses 12-bit recording at two-thirds rate. <b>Sunny</b> uses 12-bit recording at half rate. Grain duration and look-back controls keep their musical timing."),
          P("With the default assignment, tap FREEZE for reverse playback and tap MOD SYNC while holding ALT to hold the recording. Tap DELAY SYNC with ALT for crossed feedback. Hold DELAY SYNC alone about 1 second to clear. MOD SYNC alone toggles triplets."),
          P("In a native model, hold ALT alone. FREEZE shows recent load, DELAY SYNC shows peak Digi load, and MOD SYNC latches Digi timing pressure. In options, the white MOD light marks the overlay and a brief green flash confirms a saved change."), credit_short)

r1 = page("Model settings and live reverse", "A playing reference for 1.3.5.0+c. Start here to combine stock delay behaviour with Seal Eggs features.",
          open_options, options, H("Model voicing and the NOISE knob"),
          pairs("Choice", "Behaviour", [
            ["Noise / Character", "Noise retains native hiss and crackle. Character assigns BRIBERY's second tone control to NOISE. Tape gains midrange grit, BBD sputters and drops out, and Digi introduces buffer glitches and octave fragments. COLOR remains available."],
            ["Tape Bright", "Removes two internal tone shelves, lifting upper frequencies by roughly 3-5.5 dB above 1 kHz. Tape Bright is independent of the global bright/dark drive setting selected at power-on."],
            ["Tape Fast pickup", "Speeds the response to TIME moves by about five times. Try it with Bright off to keep the darker Tape tone."],
            ["BBD Light", "Opens the internal filter ceiling to 12 kHz from the stock 4.2 kHz. Long BBD times still darken as the simulated clock slows. Use the native LP slider to trim the top end."],
          ], .245, True),
          H("Reverse and saving"), P("Tap FREEZE to reverse the live delay. Input and feedback continue, and TIME edits take effect at a slice boundary. Hold ALT + TAP together for about a second to change the button's role to native Freeze. On the next boot the tap operates Reverse again, initially off."),
          P("Edits apply on short releases in options. MOD SYNC breathes white and alternates teal or orange if an alternate engine is open. A green acknowledgment follows a successful changed-settings write. New model options default to stock. A previous Seal Eggs Character preference seeds all three models. A factory reset also resets the new options."))

r2 = page("Digi TIME and Pitch Throw", "Use these four responses in native Digi. The DELAY SYNC button selects the response inside options and returns to its clock function outside.",
          pairs("DELAY SYNC in options", "What happens to the sound", [
              ["{Blue} Stock", "The original forward Digi reader crossfades on a time change. Engaging reverse uses the reverse reader temporarily and preserves your saved choice."],
              ["{Cyan} Smooth", "TIME movement produces a continuous pitch bend. The response follows the slider or CV. A rapid jump still gives a sharp change."],
              ["{Amber} Stepped", "BRIBERY's original Digi Doppler. Large changes move in semitones and can reach about two octaves. Smooth and Stepped use the same delay follower."],
              ["{Magenta} Throw", "The ordinary Digi echo continues while one additional stereo voice bends independently. It reads the existing history and fades into silence. MIX controls its audible wet level."],
          ], .265), run_throw, recharge, H("Timing and interaction"),
          pairs("During the throw", "What to expect", [
              ["Direction", "After the short rest, a move of at least 2% must sustain its direction for about 20 ms. The launched voice begins near the original pitch, rising or falling toward five semitones."],
              ["Tail / feedback", "Later slider movement leaves the launched trajectory alone. Existing echoes can be heard in its source. The new voice itself is mixed outside the feedback path. FOG can ring beyond the voice's two-second fade."],
              ["Pickup / re-arm", "A deliberate ALT hold of at least about 250 ms engages quiet repositioning. After release, the slider must reach the saved position for manual time to resume. CV and modulation continue. Rest TIME again to re-arm a throw."],
              ["Changing context", "Reverse, native Freeze or entering options inhibits new throws and fades the running voice. Switching model, response or engine clears the temporary pickup. The response choice survives power-off."],
          ], .235, True))

r3 = page("Seal Beads", "A granular instrument behind DIGI. It writes incoming stereo audio to a buffer and plays short, independently pitched windows of that recording.",
          alt_engines, H("Grain controls"), T(["Panel control", "Free timing", "With DELAY SYNC"],[.20,.405,.395], [
              ["TIME RANGE + TIME/L", "Short / Med / Long reach back about 1 / 4 / 16 seconds. TIME chooses the read position with finer travel near the present.", "Look-back windows span 1 / 4 / 16 pulses."],
              ["WIDTH/R", "Grain duration, about 20 ms to 8 seconds.", "Duration from 1/16 to 16 pulses."],
              ["MOD RATE", "Pitch across ±2 octaves, with extra travel at musical intervals.", "Same pitch control."],
              ["MOD DEPTH", "Density from off to about 40 starts per second.", "Grain starts per pulse are off, 1/8, 1/4, 1/2, 1, 2, 3, 4, 6, 8."],
              ["MOD knob", "Grain overlap. More overlap lets earlier grains ring across later onsets.", "Blend remains available while onsets follow the grid."],
              ["COLOR", "Envelope from soft at the bottom through a bell around noon to hard rectangular edges at the top.", "Same envelope control."],
              ["NOISE", "Sprays read positions across the selected look-back range and varies grain onset.", "Spray uses clocked slices."],
          ], True), H("Recording media"), pairs("DIGI / TAP in options", "Recording path", [
              ["{Blue} Digital", "The original Seal Beads digital recording quality."],
              ["{Green} Cold Digital", "12-bit recording with the granular engine at two-thirds rate, about 31.25 kHz on Sealegs. Redux converts stereo audio into and out of this rate."],
              ["{Amber} Sunny Tape", "12-bit recording with half-rate filtering and playback, about 23.44 kHz internally. Grain timing is compensated for the slower engine."],
          ],.30,True), quality_pending,
          P("Tap MOD SYNC for triplets. With the default button assignment, tap FREEZE for reverse grains (magenta), or hold ALT and tap MOD SYNC to freeze the recording (blue). The button-role swap interchanges these controls. PONG sums the inputs and spreads grains, T:W pans stereo grains, and L/R retains channel placement."))

r4 = page("Seal Microloops", "BRIBERY's BBD alternate engine uses captured loops. TIME RANGE selects an algorithm. RATE chooses a variation in four zones from bottom to top.",
          alt_engines, H("Algorithms and variations"),
          T(["Range", "A", "B", "C", "D"], [.16,.21,.21,.21,.21], [
              ["SHORT<br/>Drone", "Loop length breathes down and up.", "Sub-octave loop with a broad, slow low-pass sweep.", "Each new capture rings through a different resonant band.", "Louder input makes the loop shorter, softer input lets it open."],
              ["MED<br/>Shuffle", "Each step gets a low-pass setting.", "Some steps replay at half speed. A filtered low octave enters above 90% DEPTH.", "Add overlapping layers with resonant filter sweeps.", "A double-time layer joins, then a crushed sub-octave."],
              ["LONG<br/>Octaves", "Normal-speed loop plus an upper octave.", "Normal-speed loop plus a lower octave.", "All loops play an octave up.", "Layers span half, normal, double and quadruple speed."],
          ],True), H("Panel controls"), pairs("Control", "Microloops mapping", [
              ["TIME/L", "Loop length or Shuffle step time, about 25 ms to 2 s free. Synced, the ten positions cover 1/16, 1/8, 3/16, 1/4, 3/8, 1/2, 3/4, 1, 1.5 and 2 incoming pulses. Triplets multiply the length by 2/3."],
              ["WIDTH/R", "Sets how many repeats precede a fresh capture or Shuffle pattern, from 1 to 64. In Drone it sets release from roughly 0.4 to 20 seconds, with indefinite sustain at maximum."],
              ["MOD RATE / DEPTH", "Choose A, B, C or D near 12%, 38%, 62% or 88% of RATE travel. DEPTH increases activity. In Octaves it adds voices, and in Shuffle it adds the selected variation's layers or filtering."],
              ["MOD / COLOR", "MOD controls overlap between passes. COLOR shapes the edges, from round through bell-shaped to hard stutters."],
              ["NOISE / FEEDBACK", "NOISE scatters capture points. In Shuffle it can also add rests, repeat steps and reverse them. FEEDBACK returns the result into the loop recording."],
          ],.245,True),
          P("HP and LP filter the loops and their feedback. L/R preserves placement. T:W and PONG spread the loops across stereo. Tap FREEZE for reverse at the default assignment. Hold ALT and tap MOD SYNC to hold the recording, or tap DELAY SYNC with ALT for crossed feedback. A long solo DELAY SYNC clears the recording."))

r5 = page("Patches and diagnostics", "Use a stable input, a known clock and the fully wet return to check what the alternate engine is playing.",
          start_micro, T(["Microloops setting", "RATE / DEPTH", "TIME / WIDTH", "Listen for"], [.23,.21,.20,.36], [
              ["MED · Shuffle A", "12% / 50%", "55% / 15%", "Drum slices on 250 ms steps."],
              ["LONG · Octaves A", "12% / 0%, then 60%", "75% / 15%", "One 500 ms loop first. Raising DEPTH adds pitched layers."],
              ["MED · B/C/B", "40%, 60%, 40% / DEPTH 100%", "55% / 15%", "The extra bass layer drops out in C. C still produces wet sound."],
          ],True),
          P("Percentages run from minimum to maximum. With DRIVE in DLY, its minimum silences the wet path. If a patch stalls or sounds unexpectedly fast, tap DELAY SYNC off and compare the same sliders. Unplugging CLK can leave the last period active. A 120 BPM square wave counted both edges in an emulator check. A roughly 10 ms trigger per beat gave the intended tempo."),
          H("A first Beads patch"), P("Feed a repeating phrase into DIGI and select a Beads quality in options. Save, then enter Beads. Choose SHORT with sync off, set MOD RATE near the centre and raise DEPTH from zero. Try WIDTH around one quarter, MOD at halfway and NOISE low. Raise TIME to hear earlier material. Re-entering for another quality clears the old recording."),
          H("Read the timing indicators"), P("Outside options, hold FREEZE/ALT alone on a native Tape, BBD or Digi delay. The previous Beads/Microloops indicators remain available in their engines."),
          pairs("LED held under ALT", "Interpretation", [
              ["FREEZE · current load", "Recent callback load for the current audio path. Green below 90%, yellow from 90%, orange from 95%, red near 99% or a late start."],
              ["DELAY SYNC · Digi peak", "Worst native Digi load since boot. Uses the same 90%, 95% and 99% bands."],
              ["MOD SYNC · Digi timing", "Green indicates valid measurements with no near-deadline or late-start event. Red latches a recorded event. Blue on DELAY/MOD means no Digi samples yet. Magenta means the measurement is unavailable or invalid."],
          ],.30,True),
          H("Sources and credits"), credit,
          P('<link href="https://intellijel.com/shop/eurorack/sealegs/" color="#165F56"><u>Intellijel Sealegs and official manual</u></link>  ·  <link href="https://www.thisisbribery.com/sealeggs/" color="#165F56"><u>BRIBERY’s Seal Eggs</u></link>  ·  <link href="https://vwal.github.io/seal-eggs-redux/" color="#165F56"><u>Redux patcher and flasher</u></link>'))

r6 = page("Install or restore firmware", "Patch your original Intellijel file directly on the Redux site. Keep the stock file for recovery.",
          H("Prepare the release file"),
          pairs("Step", "On the computer", [
              ["1  Get stock", 'Download the original <b>Sealegs.1.3.5.0.bin</b> from Intellijel’s firmware directory at <link href="https://github.com/intellijel/firmware/tree/master/bin" color="#165F56"><u>github.com/intellijel/firmware/tree/master/bin</u></link>.'],
              ["2  Build Redux", 'Open the <link href="https://vwal.github.io/seal-eggs-redux/" color="#165F56"><u>Redux release site</u></link>. In the patcher, select your official <b>Sealegs.1.3.5.0.bin</b>. Build the patched image. The browser checks the stock file, applies the patch locally and verifies the result.'],
              ["3  Save the result", 'Download <b>Sealegs.1.3.5.0+c.bin</b>. Choose this saved file in the flasher when you are ready to write it to the module.'],
          ], .24),
          H("Flash the module"),
          pairs("Step", "At the rack", [
              ["4  Enter BOOT", "Use a desktop browser with WebUSB, such as Chrome or Edge. Power the rack off, connect a USB data cable to the rear of Sealegs and hold its rear BOOT button while powering the rack on."],
              ["5  Connect and write", "Confirm the attached module is Sealegs. In the browser's device picker, select the STM32 bootloader or DFU device. Start the flash and keep the computer awake, cable connected and module powered through readback verification."],
              ["6  Restart", "After the page reports a full match, start the verified firmware. Power the rack off, disconnect USB, then power on normally. Check the MOD SYNC options layer and audio."],
          ], .24),
          H("Back to the stock firmware"), P('Open the official Intellijel Firmware Updater at <link href="https://intellijel.github.io/firmware/" color="#165F56"><u>intellijel.github.io/firmware/</u></link>. Select <b>Sealegs</b> and follow the instructions to reflash your module. If a write or readback fails, reconnect in BOOT mode and repeat the complete write before restarting.'),
          N("Release identity", "The flasher identifies Seal Eggs Redux 1.3.5.0+c by its SHA-256 digest. The official stock and Redux images are both 589,964 bytes."),
          P("Seal Eggs Redux is independent community firmware, supplied as-is. Flash at your own risk. Emulation and physical-module tests covered the release. Individual patches, USB equipment and clock sources can behave differently. Flashing replaces program memory. Record any settings you need before changing firmware."))

DOCUMENTS = [
    ("quick-reference", "Quick reference", [q1, q2, q3, q4]),
    ("new-features", "New features only", [n1, n2]),
    ("feature-reference", "Feature reference", [r1, r2, r3, r4, r5, r6]),
]
