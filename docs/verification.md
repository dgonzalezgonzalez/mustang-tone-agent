# Verification status

This record distinguishes software checks from physical demonstration. Live validation is ongoing; it is not a claim of measured song matching.

## Completed checks

- Twenty-seven automated tests pass for catalog refusal, recording quality, no microphone fallback, preservation of a named existing song preset, serialization, duplicate requests, cancellation, trial bounds, best retention and automatic restoration after a worse final trial, restore failures, pedal-triggered slot changes, bypass readback, safe save navigation, starred current slots, keyboard dismissal, truncated names and HTTP authentication/origin checks.
- React/TypeScript production build passes; Ruff passes.
- GT40 USB input detected under Windows WASAPI, 48 kHz stereo.
- Android Fender Tone 5.1.3 selected Studio Preamp, British 70s, Chromatic Pitch Shifter and Sine Chorus. Ordered three-block chain was read back through model titles.
- Native parameter drawers read successfully. Pitch was set to +350 cents and verified numerically. Effect insertion/removal and amp replacement were demonstrated in empty slot 172.
- The complete Atom City Queen AI plan was applied through Codex MCP and all 13 requested values matched numeric readback. The named preset has been physically saved in slot 172; service-level reload verification is ongoing.
- Both demo effects were bypassed and returned to active through Fender Tone, with displayed-state readback. Preset application and reload now verify these states. Small-range controls use verified increment buttons; coarse interpolation is reserved for ranges requiring more than 100 increments.
- Empty slot 172 was restored to Studio Preamp defaults, saved, switched away from, reloaded and numerically verified: volume 10.0; gain, treble, middle and bass 5.5. The complete song chain still requires its final save/reload test.
- The official studio recording's short excerpt was acquired locally and processed with Demucs `htdemucs_6s`. Guitar output passed basic quality checks. Audio and weights are private and are not published.
- Tev 0.8B: 26/40 correct, warm p95 1.68 seconds. Tev 4B: 32/40 correct, warm p95 6.38 seconds. Neither is enabled automatically.
- Codex initialized the registered local MCP server and discovered its tool inventory. Python SDK stdio and Streamable HTTP checks pass. An independent JavaScript SDK client discovered all 15 tools and called capabilities successfully.
- The public repository is published at https://github.com/dgonzalezgonzalez/mustang-tone-agent. The Windows installer and desktop launcher pass; a fresh authenticated browser load reports no console errors or warnings.

## Remaining live acceptance

- Finish applying Atom City Queen AI through the service, save it and verify parameters after an actual preset reload.
- Confirm effect states survive the final song preset reload; physical master volume has not been touched by the adapter.
- Record two baseline takes with the player, compare the same phrase, refine within bounds, retain the best candidate and save it.
- Confirm Bluetooth amplifier control survives recording rather than inferring it from the phone's USB connection.
- Exercise MGT-4 preset selection and firmware-specific category bypass with the player.
- Browser workbench renders correctly; installer and desktop launcher checks pass. Continue browser workflow checks after the song preset is applied.

The pre-existing slot 171 song preset has not been edited or used to infer the demo settings. No similarity acceptance is reported before usable reference audio, actual playing and listening feedback exist.
