import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Guitar,
  Cable,
  Bluetooth,
  Play,
  Square,
  Save,
  RotateCcw,
  Plus,
  Check,
  ArrowRight,
  AudioLines,
  Copy,
  SlidersHorizontal,
} from "lucide-react";
import "./style.css";

type Profile = { guitar: string; pickup: string; tuning: string };
type Plan = {
  name: string;
  slot: number;
  section: string;
  chain: {
    model: string;
    kind: string;
    enabled: boolean;
    parameters: Record<string, number | string>;
  }[];
  rationale: string;
  setup_recommendation: string;
  limitations: string[];
};
type Session = {
  id: string;
  song: string;
  artist: string;
  slot: number;
  profile: Profile;
  status: string;
  section: string;
  current_plan: Plan | null;
  baseline_ids: string[];
  takes: string[];
  trials: number;
  max_trials: number;
  replacements: number;
  reference_id: string | null;
  reference_quality: string | null;
  best_take: string | null;
  setup_recommendation: string;
  limitations: string[];
};
type Job = { id: string; status: string; message: string };
type State = {
  sessions: Session[];
  presets: { id: string; plan: Plan }[];
  jobs: Job[];
  active_job: string | null;
};
let access =
  new URLSearchParams(location.hash.slice(1)).get("token") ||
  sessionStorage.getItem("mustang-token") ||
  "";
if (access) {
  sessionStorage.setItem("mustang-token", access);
  history.replaceState(null, "", location.pathname);
}
async function api(path: string, body?: unknown): Promise<any> {
  const res = await fetch("/api" + path, {
    method: body === undefined ? "GET" : "POST",
    headers: {
      Authorization: "Bearer " + access,
      ...(body === undefined ? {} : { "Idempotency-Key": crypto.randomUUID() }),
      ...(body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
    },
    body:
      body === undefined
        ? undefined
        : body instanceof FormData
          ? body
          : JSON.stringify(body),
  });
  const value = await res.json();
  if (!res.ok) throw new Error(value.detail || res.statusText);
  return value;
}
function Player({ id, label }: { id: string; label: string }) {
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    let live = true;
    let object = "";
    fetch("/api/audio/" + id + "/play", {
      headers: { Authorization: "Bearer " + access },
    })
      .then(async (r) => {
        if (!r.ok) throw new Error("Audio unavailable");
        return r.blob();
      })
      .then((b) => {
        object = URL.createObjectURL(b);
        if (live) setUrl(object);
      })
      .catch((e) => setError(e.message));
    return () => {
      live = false;
      if (object) URL.revokeObjectURL(object);
    };
  }, [id]);
  return (
    <div className="player">
      <span>{label}</span>
      {error ? (
        <small>{error}</small>
      ) : (
        <audio controls src={url} preload="metadata" />
      )}
    </div>
  );
}
function Card({
  step,
  title,
  wide,
  children,
}: {
  step: string;
  title: string;
  wide?: boolean;
  children: React.ReactNode;
}) {
  return (
    <section className={"card " + (wide ? "wide" : "")}>
      <div className="card-heading">
        <span className="step">{step}</span>
        <h2>{title}</h2>
      </div>
      {children}
    </section>
  );
}
function App() {
  const [state, setState] = useState<State>({
    sessions: [],
    presets: [],
    jobs: [],
    active_job: null,
  });
  const [selected, setSelected] = useState("");
  const [connections, setConnections] = useState<any>();
  const [error, setError] = useState("");
  const [syncError, setSyncError] = useState("");
  const [notice, setNotice] = useState("");
  const [pending, setPending] = useState(false);
  const [song, setSong] = useState("Atom City Queen");
  const [artist, setArtist] = useState("Failure");
  const [slot, setSlot] = useState(172);
  const [profile, setProfile] = useState<Profile>({
    guitar: "Squier Telecaster",
    pickup: "bridge",
    tuning: "E A D G B E (standard)",
  });
  const [url, setUrl] = useState("https://www.youtube.com/watch?v=GbDRNvLlMuU");
  const [permitted, setPermitted] = useState(false);
  const [start, setStart] = useState(0);
  const [planText, setPlanText] = useState("");
  const [feedback, setFeedback] = useState("");
  const [direction, setDirection] = useState("brighter");
  const [take, setTake] = useState<any>();
  const s = state.sessions.find((v) => v.id === selected) || state.sessions[0];
  const busy = pending || !!state.active_job;
  const job =
    state.jobs.find((j) => j.id === state.active_job) || state.jobs[0];
  const path = (a: string) => "/sessions/" + s?.id + "/" + a;
  async function refresh() {
    try {
      setState(await api("/state"));
      setSyncError("");
    } catch (e) {
      setSyncError((e as Error).message);
    }
  }
  async function run(action: () => Promise<any>, message = "") {
    setError("");
    setNotice("");
    setPending(true);
    try {
      const r = await action();
      setNotice(message);
      await refresh();
      return r;
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setPending(false);
    }
  }
  useEffect(() => {
    if (!access) return;
    refresh();
    api("/connections")
      .then(setConnections)
      .catch((e) => setError(e.message));
    const timer = setInterval(refresh, 2000);
    return () => clearInterval(timer);
  }, []);
  useEffect(() => {
    setTake(null);
    if (s?.takes.length)
      api("/audio/" + s.takes.at(-1))
        .then(setTake)
        .catch(() => {});
  }, [s?.id, s?.takes.length]);
  async function capture(role: string) {
    document.querySelectorAll("audio").forEach((a) => a.pause());
    await run(() =>
      api(path("capture"), { role, ready: true, permitted, seconds: 10 }),
    );
  }
  async function copyPrompt() {
    if (!s) return;
    try {
      await navigator.clipboard.writeText(
        `Use Mustang Tone Agent MCP to research ${s.song} by ${s.artist}. Continue session ${s.id}, slot ${s.slot}, guitar ${s.profile.guitar}, ${s.profile.pickup} pickup, ${s.profile.tuning}. Read get_capabilities. Use only observed models and parameters. Design and apply a fresh ordered chain, verify it, and explain pickup recommendations and limitations. Wait for me to press Ready before recording. Preserve existing presets.`,
      );
      setNotice("Copied. Paste into your connected AI agent.");
    } catch {
      setError("Clipboard unavailable in this browser.");
    }
  }
  if (!access)
    return (
      <div className="gate">
        <Guitar size={44} />
        <h1>Mustang Tone Agent</h1>
        <p>Use the desktop launcher to connect securely.</p>
        <label>
          Local access token
          <input
            type="password"
            onChange={(e) => {
              access = e.target.value;
            }}
          />
        </label>
        <button
          onClick={() => {
            sessionStorage.setItem("mustang-token", access);
            location.reload();
          }}
        >
          Connect
        </button>
      </div>
    );
  return (
    <div className="app">
      <aside>
        <div className="brand">
          <Guitar />
          <span>
            MUSTANG<span className="brand-sub">TONE AGENT</span>
          </span>
        </div>
        <div className="nav active">
          <SlidersHorizontal size={18} />
          Tone workbench
        </div>
        <div className="side-label">YOUR SESSIONS</div>
        {state.sessions.map((v) => (
          <button
            key={v.id}
            className={"session-link " + (s?.id === v.id ? "selected" : "")}
            onClick={() => setSelected(v.id)}
          >
            <span>{v.song}</span>
            <small>
              {v.artist} · slot {v.slot}
            </small>
          </button>
        ))}
        <div className="side-label">SAVED PRESETS</div>
        {state.presets.map((p) => (
          <div className="session-link" key={p.id}>
            <span>{p.plan.name}</span>
            <small>Verified · slot {p.plan.slot}</small>
          </div>
        ))}
        <div className="side-bottom">
          <span className="dot" />
          Local processing<p>GT40 · MGT-4 · USB matching</p>
        </div>
      </aside>
      <main>
        <header>
          <div>
            <div className="eyebrow">FENDER MUSTANG GT40</div>
            <h1>Your next guitar sound.</h1>
            <p>Choose a song. Shape the tone. Play, compare, refine.</p>
          </div>
          <button
            className="secondary"
            disabled={busy}
            onClick={() =>
              run(async () => setConnections(await api("/connections")))
            }
          >
            <Cable size={16} />
            Check connections
          </button>
        </header>
        <div className="connection-strip">
          <span
            className={
              connections?.phone.connected ? "connected" : "disconnected"
            }
          >
            <Bluetooth size={15} />
            {connections?.phone.connected
              ? "Phone USB connected"
              : "Phone unavailable"}
          </span>
          <span
            className={
              connections?.audio.connected ? "connected" : "disconnected"
            }
          >
            <AudioLines size={15} />
            {connections?.audio.connected
              ? "Fender USB ready"
              : "USB audio unavailable"}
          </span>
          <span
            className={
              connections?.amp_control?.connected ? "connected" : "disconnected"
            }
          >
            {connections?.amp_control?.connected
              ? "Amp Bluetooth ready"
              : "Amp Bluetooth unverified"}
          </span>
          <span className="muted">No paid AI calls</span>
        </div>
        {(error || syncError) && (
          <div className="alert error" role="alert">
            {error || syncError}
          </div>
        )}
        {notice && <div className="alert success">{notice}</div>}
        {job && (
          <div className={"job " + job.status} aria-live="polite">
            <span className="dot" />
            {job.message}
            <small>{job.status}</small>
            {state.active_job && (
              <button
                className="stop"
                onClick={() => run(() => api("/stop", {}))}
              >
                <Square size={13} />
                Stop
              </button>
            )}
          </div>
        )}
        <div className="grid">
          <Card step="01" title="The song & your guitar">
            <div className="fields two">
              <label>
                Song
                <input value={song} onChange={(e) => setSong(e.target.value)} />
              </label>
              <label>
                Artist
                <input
                  value={artist}
                  onChange={(e) => setArtist(e.target.value)}
                />
              </label>
            </div>
            <div className="fields two">
              <label>
                Guitar
                <input
                  value={profile.guitar}
                  onChange={(e) =>
                    setProfile({ ...profile, guitar: e.target.value })
                  }
                />
              </label>
              <label>
                Pickup
                <select
                  value={profile.pickup}
                  onChange={(e) =>
                    setProfile({ ...profile, pickup: e.target.value })
                  }
                >
                  <option>bridge</option>
                  <option>neck</option>
                  <option>both</option>
                </select>
              </label>
            </div>
            <div className="fields two">
              <label>
                Tuning
                <input
                  value={profile.tuning}
                  onChange={(e) =>
                    setProfile({ ...profile, tuning: e.target.value })
                  }
                />
              </label>
              <label>
                Empty slot
                <input
                  type="number"
                  min={1}
                  max={200}
                  value={slot}
                  onChange={(e) => setSlot(+e.target.value)}
                />
              </label>
            </div>
            <button
              disabled={busy}
              onClick={() =>
                run(async () => {
                  const v = await api("/sessions", {
                    song,
                    artist,
                    slot,
                    profile,
                  });
                  setSelected(v.id);
                  return v;
                })
              }
            >
              <Plus size={16} />
              Create session
            </button>
            <p className="hint">
              Start in a verified Empty preset. Your existing presets are
              preserved.
            </p>
          </Card>
          <Card step="02" title="The reference">
            <label>
              Original recording URL
              <input value={url} onChange={(e) => setUrl(e.target.value)} />
            </label>
            <div className="reference-actions">
              <a href={url} target="_blank" rel="noreferrer">
                Listen to recording ↗
              </a>
              <label className="compact">
                Start at
                <input
                  type="number"
                  min={0}
                  value={start}
                  onChange={(e) => setStart(+e.target.value)}
                />
                seconds
              </label>
            </div>
            <label className="check">
              <input
                type="checkbox"
                checked={permitted}
                onChange={(e) => setPermitted(e.target.checked)}
              />
              I may process this reference recording.
            </label>
            <div className="button-row">
              <button
                disabled={busy || !s || !permitted}
                onClick={() =>
                  run(() =>
                    api(path("reference"), {
                      url,
                      source: "Original recording selected by user",
                      permitted,
                      start,
                      duration: 20,
                    }),
                  )
                }
              >
                Get excerpt
              </button>
              <label
                className={
                  "file-button " + (busy || !s || !permitted ? "disabled" : "")
                }
              >
                Import audio
                <input
                  type="file"
                  accept="audio/*"
                  disabled={busy || !s || !permitted}
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) {
                      const b = new FormData();
                      b.append("file", f);
                      b.append("permitted", String(permitted));
                      run(() => api(path("upload"), b));
                    }
                  }}
                />
              </label>
              <button
                className="secondary"
                disabled={busy || !s || !permitted}
                onClick={() => capture("reference")}
              >
                Capture playback
              </button>
            </div>
            {s?.reference_id ? (
              <>
                <Player
                  id={s.reference_id}
                  label={
                    s.reference_quality === "separated"
                      ? "Extracted guitar · level matched"
                      : "Reference · level matched"
                  }
                />
                <button
                  className="secondary"
                  disabled={busy}
                  onClick={() => run(() => api(path("separate"), {}))}
                >
                  Separate guitar locally
                </button>
                <p className="hint">
                  Guitar separation is experimental and may combine layers.
                </p>
              </>
            ) : (
              <p className="hint">
                Without usable reference audio, use research and listening
                feedback. No score will be invented.
              </p>
            )}
          </Card>
          <Card step="03" title="The sound design" wide>
            <div className="tone-top">
              <div>
                <h3>
                  {s?.current_plan?.name || "Start with an expert tone plan"}
                </h3>
                <p>
                  {s?.current_plan?.rationale ||
                    "Your AI agent researches the song and selects verified GT40 models."}
                </p>
              </div>
              <button className="secondary" disabled={!s} onClick={copyPrompt}>
                <Copy size={15} />
                Copy agent request
              </button>
            </div>
            <div className="chain">
              {s?.current_plan?.chain.map((b, i) => (
                <React.Fragment key={i}>
                  {i > 0 && <ArrowRight className="chain-arrow" size={17} />}
                  <div className={"block " + b.kind}>
                    <small>{b.kind}</small>
                    <strong>{b.model}</strong>
                    <span>
                      {Object.entries(b.parameters)
                        .map(([k, v]) => `${k} ${v}`)
                        .join(" · ")}
                    </span>
                  </div>
                </React.Fragment>
              )) || (
                <div className="empty-chain">
                  <Guitar />
                  Your chain appears after verified application.
                </div>
              )}
            </div>
            <div className="setup">
              <strong>Playing setup</strong>
              <span>
                {s?.setup_recommendation ||
                  "Squier Telecaster · bridge pickup · standard tuning"}
              </span>
            </div>
            <p className="hint">
              {(s?.current_plan?.limitations || s?.limitations || []).join(
                " · ",
              )}
            </p>
            <details>
              <summary>Load a plan from your agent</summary>
              <textarea
                aria-label="Tone plan JSON"
                value={planText}
                onChange={(e) => setPlanText(e.target.value)}
                placeholder="Paste TonePlan JSON"
              />
              <div className="button-row">
                <button
                  disabled={busy || !s || !planText}
                  onClick={() =>
                    run(() =>
                      api(path("apply"), {
                        plan: JSON.parse(planText),
                        request_id: crypto.randomUUID(),
                      }),
                    )
                  }
                >
                  Apply & verify
                </button>
                <button
                  className="secondary"
                  disabled={busy || !s}
                  onClick={() =>
                    run(async () => {
                      const p = await api("/demo-plan");
                      p.slot = s.slot;
                      setPlanText(JSON.stringify(p, null, 2));
                    }, "Demo loaded into the plan editor.")
                  }
                >
                  Load Failure demo
                </button>
              </div>
            </details>
          </Card>
          <Card step="04" title="Play & compare">
            <div className="take-instruction">
              <AudioLines size={30} />
              <div>
                <strong>Play the same short phrase</strong>
                <p>
                  Reference playback stops first. Three-second countdown, then
                  ten seconds of guitar.
                </p>
              </div>
            </div>
            <div className="counts">
              <div>
                <b>
                  {s?.baseline_ids.length || 0}
                  <span>/2</span>
                </b>
                <small>baseline takes</small>
              </div>
              <div>
                <b>
                  {s?.trials || 0}
                  <span>/{s?.max_trials || 6}</span>
                </b>
                <small>adjustment trials</small>
              </div>
              <div>
                <b>{Math.max(0, 2 - (s?.replacements || 0))}</b>
                <small>retakes remaining</small>
              </div>
            </div>
            <button
              className="record"
              disabled={busy || !s?.current_plan || s.status === "complete"}
              onClick={() =>
                capture(s!.baseline_ids.length < 2 ? "baseline" : "trial")
              }
            >
              <Play size={16} />
              Ready — record my guitar
            </button>
            {take && (
              <div className="comparison">
                <strong>
                  {take.features.valid
                    ? "Take recorded"
                    : "Take needs replacement"}
                </strong>
                {take.features.issues?.length > 0 && (
                  <p>{take.features.issues.join(", ")}</p>
                )}
                {take.comparison ? (
                  <div className="distance">
                    {take.comparison.distance}
                    <span>feature distance · lower is closer</span>
                  </div>
                ) : (
                  <p>No measured reference comparison available.</p>
                )}
                <p className="hint">
                  Diagnostic distance, not a similarity percentage. Playing and
                  separation affect the result.
                </p>
              </div>
            )}
            {s?.takes.length ? (
              <Player
                id={s.takes.at(-1)!}
                label="Latest take · level matched"
              />
            ) : null}
            {s?.best_take && s.best_take !== s.takes.at(-1) && (
              <Player id={s.best_take} label="Best measured take" />
            )}
          </Card>
          <Card step="05" title="Refine & keep">
            <label>
              Your listening notes
              <textarea
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                placeholder="Too bright? More drive?"
              />
            </label>
            <div className="button-row">
              <button
                className="secondary"
                disabled={busy || !s}
                onClick={() =>
                  run(() => api(path("feedback"), { description: feedback }))
                }
              >
                Save feedback
              </button>
              <button
                disabled={busy || !s?.current_plan}
                onClick={() =>
                  run(
                    () => api(path("feedback"), { accepted: true }),
                    "Accepted. Refinement stopped.",
                  )
                }
              >
                <Check size={16} />
                Good enough
              </button>
            </div>
            <div className="fields two">
              <label>
                Adjustment
                <select
                  value={direction}
                  onChange={(e) => setDirection(e.target.value)}
                >
                  <option value="brighter">Brighter</option>
                  <option value="darker">Darker</option>
                  <option value="gain_up">More drive</option>
                  <option value="gain_down">Cleaner</option>
                  <option value="modulation_up">More modulation</option>
                  <option value="modulation_down">Less modulation</option>
                </select>
              </label>
              <button
                className="secondary align-end"
                disabled={
                  busy ||
                  !s ||
                  s.baseline_ids.length < 2 ||
                  s.status === "complete"
                }
                onClick={() =>
                  run(async () => {
                    const c = await api(path("candidate"), { direction });
                    setPlanText(JSON.stringify(c.plan, null, 2));
                  }, "Candidate loaded. Apply it, then record a fresh take.")
                }
              >
                Propose change
              </button>
            </div>
            <div className="save-actions">
              <button
                disabled={busy || !s?.current_plan}
                onClick={() => run(() => api(path("save"), {}))}
              >
                <Save size={16} />
                Save to amplifier
              </button>
              <button
                className="secondary"
                disabled={busy || !s?.best_take}
                onClick={() => run(() => api(path("restore"), { best: true }))}
              >
                Restore best
              </button>
              <button
                className="secondary"
                disabled={busy || !s}
                onClick={() => run(() => api(path("restore"), { best: false }))}
              >
                <RotateCcw size={16} />
                Restore original
              </button>
            </div>
            <p className="hint">
              Six trials maximum. Stops after two improvements below playing
              variability, or your acceptance.
            </p>
            <details>
              <summary>MGT-4 footswitch guide</summary>
              <p>
                Firmware 3.0.43: use PRESETS mode for preset selection. Under
                MENU → FOOTSWITCH → MGT-4 → FX Assign, select First 3 (Default)
                for this demo. In EFFECTS mode, check which buttons bypass the
                pitch shifter and chorus, then restore both. Other
                configurations assign stompbox, modulation, delay and reverb
                categories; a dedicated pitch category is not documented for
                this pedal. Live pedal verification requires your participation.
              </p>
            </details>
          </Card>
        </div>
        <footer>
          Mustang Tone Agent · Independent project; not affiliated with Fender.
        </footer>
      </main>
    </div>
  );
}
createRoot(document.getElementById("root")!).render(<App />);
