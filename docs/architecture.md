# Architecture

React is served locally by a Python 3.12 FastAPI backend. SQLite stores song sessions, job results, checkpoints, reference provenance, takes and saved presets. One worker serializes all operations that touch hardware or audio. A cancellation event reaches ADB, recording and external reference/separation processes.

The stdio and authenticated Streamable HTTP MCP transports proxy the same backend. Agents receive typed capabilities, compact state and asynchronous job IDs. They do not receive arbitrary shell, tap or file-write tools. The production skill guides song research and bounded refinement; plugin manifests package discovery without coupling the backend to one agent.

Screen adapters use ADB screenshots, cropped RapidOCR reads and OpenCV node recognition. The supported portrait layout, app version, model title and preset slot are checked before changes. Numeric drawers provide readback. Large-range sliders are calibrated using two measured positions; small corrections use the observed increment buttons. Bounded retries stop on contradictory or unreadable results. Saving selects the intended slot, reloads it through an untouched empty neighbor and checks the requested chain and parameters.

Only observed, calibrated model parameters are writable. Installed app GT definitions helped establish native ranges; those proprietary assets are kept outside the repository. Amp/effect scales exposed by the current controls run from 1 to 10, rather than 0 to 10. Pitch is cents and pitch-delay time is milliseconds. Uncalibrated controls, explicit cabinet replacements and arbitrary original preset backups remain unsupported. The native hardware may offer more models or chain slots than the current adapter supports.

The song expert supplies an initial plan. Local candidates make bounded changes within the verified parameter catalog. Every candidate needs fresh playing; this design does not assume USB reamping. Two baseline takes estimate playing variability, invalid recordings consume a limited replacement allowance, and the best measured candidate remains available after a worse trial.

Feature distances measure normalized spectral shape, crest factor, envelope variability and stereo width. They cannot certify a song tone, identify all guitar layers, or separate performance from timbre. The current implementation does not separately estimate sustain decay or modulation frequency. Baseline and listening feedback limit how much weight to place on small score improvements.

Cached references and features reduce repeated AI work. Optional Tev routes narrow text feedback; it cannot plan the full song or analyze audio. The backend makes no separate paid model calls. Credentials, user recordings, copyrighted references, phone identifiers and model weights live outside source control.
