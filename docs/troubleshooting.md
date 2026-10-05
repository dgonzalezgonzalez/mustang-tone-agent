# Troubleshooting

**Phone unavailable:** unlock it, reconnect its USB cable, accept debugging authorization and open Fender Tone. Close other tools controlling the phone. The adapter requires exactly one authorized Android device.

**Unsupported Tone version or uncertain screen:** stop. Recalibrate the adapter against the installed version before writing. Do not substitute guessed tap coordinates or treat a tap as a successful change.

**Screen sleeps during verification:** the adapter periodically sends Android WAKEUP before screenshots. This leaves the screen-timeout setting unchanged. Unlock a secure lock screen yourself; the adapter stops if Fender Tone's controls cannot be verified.

**Wrong preset selected:** open the intended empty slot in Fender Tone. A named existing preset is deliberately refused. If another session owns the slot, continue it or restore its original checkpoint first.

**Partial or interrupted application:** reconnect, inspect the slot, then use Restore original. A checkpoint remains in private runtime data. Stop prevents further actions at a safe boundary; restoration is a separate operation. Restarted jobs are marked interrupted rather than silently retried.

**USB audio unavailable:** reconnect the amplifier and check Windows audio inputs. The program never records a laptop microphone as a substitute. Close applications holding the device exclusively if an audio stream fails or overflows.

**Silent/clipped take:** check the guitar cable, instrument volume, selected preset and amplifier input level. Keep reference playback stopped. Reduce preset digital volume if clipping occurs; master volume is a physical listening control and is untouched. Replacement recordings are bounded.

**Different phrase or pickup:** repeat the same notes and picking pattern. Start new baselines if you deliberately change pickup, tuning or guitar controls. Pitch-profile checks catch large differences but cannot prove that two performances are identical.

**Reference download fails:** import a recording you may process or use user-started playback capture. No login, cookies or access bypass is implemented. The preset can still be designed from artist evidence and listening notes, with audio comparison marked unavailable.

**Demucs unavailable:** run the optional separator installer. It uses CPU PyTorch in a separate environment. Weights download on the first run. Separation is approximate; audition the result before relying on its distances.

**MCP fails to connect:** start the desktop service, check `http://127.0.0.1:8765/health`, and reconnect the client. Use the absolute virtual-environment Python path. HTTP needs the local bearer token. Cloud-only clients cannot reach localhost directly.

**Tev disabled:** benchmark it. Automatic use requires the published accuracy and latency gate. Explicit adjustment controls and the external agent work without it. Neither local model analyzes audio.
