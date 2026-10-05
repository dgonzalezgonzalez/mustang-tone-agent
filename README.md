# Mustang Tone Agent

A Windows workbench and local MCP server for researching guitar tones, controlling a Fender Mustang GT40 through Fender Tone on Android, and comparing USB recordings. Your existing AI agent supplies the musical expertise. Recording, screen recognition, validation and bounded refinement run locally. No paid AI API is required.

**Hardware integration is under live validation.** This is an independent experimental project, not a Fender product. The current screen adapter targets Fender Tone **5.1.3** in portrait mode and has been developed against a GT40 running **3.0.43**. Only calibrated models and controls are writable; the full amplifier catalog is not yet automated. See [verification status](docs/verification.md).

## Install and launch

From PowerShell in the checkout:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install.ps1
```

The installer creates a Python 3.12 environment, installs pinned dependencies, builds the React interface and creates a desktop shortcut. Use `-SkipWinget` if Python 3.12, Node.js, Android Platform Tools and FFmpeg are already installed. Double-click **Start Mustang Tone Agent.cmd**, or the desktop shortcut.

Connect the amplifier by USB and connect an unlocked Android phone with USB debugging authorized. Open Fender Tone and connect it to the amp through Bluetooth. No rooting or custom phone app is needed. [Connection guide](docs/connections.md) · [Troubleshooting](docs/troubleshooting.md).

## Use with your AI agent

Start the desktop service first. For Codex:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/connect-agent.ps1 -Codex
```

The script registers the stdio MCP server and installs the small `mustang-tone` production skill. Other local MCP clients can use the absolute Python path and arguments written by `scripts/connect-agent.ps1`. Authenticated Streamable HTTP is available at `http://127.0.0.1:8765/mcp`. [Agent connection details](docs/connections.md#mcp-clients).

The backend is independent of the skill and plugin wrapper. Compatible agents share the same local service and hardware lock. A cloud-only agent cannot directly access this loopback server; it needs a separately configured connection arrangement.

## Tone workflow

1. Create a song session in a verified empty slot. The default guitar profile is a Squier Telecaster, bridge pickup, standard tuning.
2. Ask the connected agent to research the song and create a plan from `get_capabilities`. Pickup recommendations include reasons; changes to your guitar setup require new baseline takes.
3. Attach a recording you may process through a permitted public download, local import or user-started playback capture. Sources stay private. If no usable reference exists, continue with research and listening feedback without an invented score.
4. Apply the plan. Every supported change requires screen/value readback. Save performs a preset switch and reload, then verifies the chain and requested parameters.
5. Press **Ready** to record a ten-second phrase from the Fender USB input after a countdown. Repeat it for two baseline takes, then play fresh takes after candidate changes.
6. Refinement stops after six trials by default, two consecutive improvements below playing variability, acceptance, cancellation or a connection failure. At most two replacement recordings are allowed. The best measured candidate is retained and can be restored.

The app compares normalized spectrum, crest factor, envelope variability and stereo width. These are diagnostic distances, not a percentage of perceptual similarity. Sustain and modulation rate are not independently estimated in the current DSP implementation. Listening remains necessary. Reference playback and guitar takes are separate; USB playback is not assumed to reamp the guitar input.

## Failure demo

`examples/atom-city-queen.json` is a fresh starting hypothesis for **Atom City Queen AI** in slot 172. The existing user preset in slot 171 is excluded. The [official studio recording](https://www.youtube.com/watch?v=GbDRNvLlMuU) is the target. In a [direct band interview](https://www.premierguitar.com/artists/failures-monster-comeback?page=2), Failure identifies Rainbow Machine on the song; a chromatic shifted layer and sine chorus approximate part of its motion, with a driven British 70s amp. They do not reproduce regenerative pitch feedback or studio double tracking.

No verified free original guitar stem was found. Optional local Demucs `htdemucs_6s` separation is experimental and may combine guitar layers or retain other instruments. Install it with `scripts/install-separator.ps1`; model weights download separately and are excluded from this repository. The [KEXP performance](https://www.youtube.com/watch?v=wo-u4PcDbqg) is supplementary evidence, not a substitute studio target.

## Optional Tev

Ollama 0.35 or later can supply narrow text decisions through `/v1/systemone`:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/benchmark-tev.ps1 -Model tev1:4b
```

Both `tev1:0.8b` and `tev1:4b` are supported. On the development laptop, 0.8B scored 65% with warm p95 1.68 seconds; 4B scored 80% with p95 6.38 seconds on the integrated GPU. Neither passes the original automatic gate of 95% accuracy and p95 below two seconds, so both remain disabled by default. The 40-case routing test is small and does not measure audio or general reasoning. Tev never replaces parameter validation or amp readback.

## Development

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m ruff check .
cd web
npm run build
```

`scripts/test-mcp.py` exercises stdio and HTTP with the Python MCP SDK. `web/test-mcp.mjs` uses the independent JavaScript SDK. `scripts/test-codex-mcp.py` checks Codex's actual MCP initialization through its app-server protocol.

Original code is MIT licensed. Audio, device identifiers, credentials, phone screenshots, Fender app assets and model weights are excluded. Private runtime data lives under `%LOCALAPPDATA%\MustangToneAgent`, outside the checkout. [Architecture and limitations](docs/architecture.md).
