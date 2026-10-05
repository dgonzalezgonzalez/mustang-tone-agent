# Connections

## Hardware

Connect the GT40 USB port directly to the laptop. Windows must expose a **Fender Mustang-GT USB Audio** input. The app prefers WASAPI and refuses to fall back to a laptop microphone.

On Android, enable developer options and USB debugging. Connect a data-capable USB cable, unlock the phone, and accept its debugging authorization for this computer. Only one authorized Android device may be connected. The app discovers its identifier privately; it is not exposed in the capability contract or repository.

Open Fender Tone and connect to the GT40 using Bluetooth. Keep the phone in portrait orientation. Bluetooth audio playback and Bluetooth amplifier control are different functions. USB debugging connects the computer to the phone; USB audio connects the amplifier to the computer.

Before the first write, open the intended empty preset in Fender Tone. The app verifies its slot and name, reads its Studio Preamp settings and stores a checkpoint. The current adapter restores this simple empty baseline; it does not back up arbitrary existing chains. Existing named presets are refused. Physical master volume is never programmed.

## MCP clients

Launch the desktop service before connecting a client. Stdio configuration uses the checkout's absolute interpreter path:

```json
{
  "mcpServers": {
    "mustang-tone": {
      "command": "C:\\path\\to\\mustang-tone-agent\\.venv\\Scripts\\python.exe",
      "args": ["-m", "mustang.cli", "mcp"]
    }
  }
}
```

Run `scripts/connect-agent.ps1` to generate a configuration with this computer's path; its output file is ignored by Git. `-Codex` registers the server in Codex and installs the skill. Reconnect or restart your agent so it discovers the tools.

Streamable HTTP clients use `http://127.0.0.1:8765/mcp` with `Authorization: Bearer <local token>`. The private token is in `%LOCALAPPDATA%\MustangToneAgent\access.token`. Do not commit or share it. The launcher passes it to the local interface using a URL fragment, which the interface removes after storing it in the browser session.

The server listens only on loopback and checks authentication, host and origin. Do not expose it by changing the bind address. Cloud clients need a separately designed authenticated connection; public hosting is not part of v1.

## MGT-4

The development amplifier has firmware 3.0.43. Later firmware supports effect-category assignments described in Fender's September 2018 manual addendum. Inspect **MENU → FOOTSWITCH → MGT-4 → FX Assign** on the amplifier and confirm the installed firmware's actual labels. Effects-mode buttons operate assigned categories, potentially bypassing multiple effects. They are not arbitrary individual-effect buttons.

Use PRESETS mode to select presets; test returning to the saved demo. Use EFFECTS mode to test pitch/filter and modulation bypass, then restore both. Footswitch behavior requires a physical live check by the player. The app must not mark it tested merely because a preset was saved.

Sources: [Fender MGT-4 support](https://support.fender.com/hc/en-us/articles/42658477091483-How-do-I-use-the-MGT-4-4-Button-footswitch-with-the-Mustang-GT-amps), [Fender-authored 2018 addendum hosted by Kraft Music](https://files.kraftmusic.com/media/ownersmanual/Fender_Mustang_GT_Addendum_to_Owners_Manual_September_2018.pdf).
