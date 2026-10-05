---
name: mustang-tone
description: Research and recreate song-specific guitar tones on a Fender Mustang GT40 through Mustang Tone Agent MCP, including verified presets and bounded USB recording comparisons.
---

# Mustang song tones

Use Mustang Tone Agent's MCP tools. The desktop service owns hardware actions and recordings; do not send generic ADB commands or guess unsupported model names.

Read `get_capabilities` before designing a TonePlan. Only `observed=true` models and their listed parameters/units are writable. Model availability does not imply that every parameter is calibrated. Consult primary artist/producer evidence; distinguish documented equipment from inferred approximations.

The user's default is Squier Telecaster, bridge pickup, standard E–A–D–G–B–E tuning, volume/tone at 10. Recommend a different pickup when useful, with a brief audible reason. Never assume they changed pickup or tuning until confirmed.

Continue the provided session or create one in a preset explicitly named Empty. Never use the user's previous song preset as a starting point. Design the dominant guitar part first, with additional song sections in separate sessions/empty slots when necessary. A studio's layered guitar production may exceed one GT40 chain.

Apply the ordered plan through `apply_preset` with a fresh request_id. Poll its job with reasonable intervals until complete/failed. Completion must include readback; stop on uncertain screens or disconnected hardware. Report unsupported parts rather than inventing settings. Save through `save_preset`, which verifies reload.

Reference order: authorized original guitar stem; analyzable original studio recording; published equipment evidence and listening feedback. Prefer free original sources. Covers and live recordings must not silently replace the studio target. Attach only references the user may process; no account/access bypass. Demucs guitar stems remain approximations.

Never start a take until the user is ready. They can press Ready in the desktop app. Two repeat baseline phrases establish playing variability; subsequent takes evaluate bounded changes. Suggest one group at a time: amp/gain, EQ, pitch/modulation, delay/reverb. Keep pickup, guitar controls, tuning and phrase consistent while comparing.

Use local candidates and compact numeric summaries instead of repeatedly analyzing screenshots/audio with a hosted model. Measurements are feature distances, not perceptual similarity percentages. No reference means no measured song similarity. Six trials, two invalid-take replacements, and two sub-variability improvements bound each section. Accepting stops refinement. Retain/restore the best verified take when appropriate.

MGT-4 assignments follow the hardware's documented modes/categories. Do not invent arbitrary individual-effect mappings or assume USB audio can reamp the guitar input. Verify footswitch behavior with the user.
