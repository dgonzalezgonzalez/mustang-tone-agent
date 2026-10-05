import io
import threading

import pytest
from PIL import Image

from mustang.models import Block, CaptureRequest, SessionRequest, TonePlan
from mustang.phone import ControlError, Phone, Text


def test_screen_reads_refresh_wake_without_changing_timeout(monkeypatch):
    phone = object.__new__(Phone)
    frame = io.BytesIO()
    Image.new("RGB", (100, 220)).save(frame, format="PNG")
    calls = []
    clock = [20.0]
    monkeypatch.setattr("mustang.phone.time.monotonic", lambda: clock[0])
    monkeypatch.setattr("mustang.phone.time.sleep", lambda _: None)

    def run(*args):
        calls.append(args)
        return frame.getvalue() if args[0] == "exec-out" else b""

    phone.run = run
    phone.screenshot()
    clock[0] = 25.0
    phone.screenshot()
    clock[0] = 31.0
    phone.screenshot()
    assert calls == [
        ("shell", "input", "keyevent", "224"),
        ("exec-out", "screencap", "-p"),
        ("exec-out", "screencap", "-p"),
        ("shell", "input", "keyevent", "224"),
        ("exec-out", "screencap", "-p"),
    ]


def test_historical_bluetooth_log_does_not_prove_current_connection():
    phone = object.__new__(Phone)
    phone.run = lambda *a: b"stack::gatt yesterday state: GATT_CH_OPEN, ACL holders com.fender.tone"
    with pytest.raises(ControlError, match="Bluetooth control"):
        phone.verify_ble()
    phone.run = lambda *a: b"  id: 0  address: PRIVATE  ch_state: GATT_CH_OPEN, ACL holders com.fender.tone"
    assert phone.verify_ble()["connected"] is True


def test_tap_without_changed_readback_cannot_report_success():
    phone = object.__new__(Phone)
    phone.cancel = threading.Event()
    phone.verify_ble = lambda: None
    phone.verify_slot = lambda *a: None
    phone.native_value = lambda *a: 5.5
    phone.panel = lambda *a: 5.5
    phone.tap = lambda *a: None
    phone.dismiss_parameter = lambda: None
    with pytest.raises(ControlError, match="did not reach"):
        phone.set_native(172, "treble", 6.0, minimum=1, maximum=10, step=0.1)


def test_bypass_tap_requires_state_readback():
    phone = object.__new__(Phone)
    phone.verify_ble = lambda: None
    phone.verify_slot = lambda *a: None
    phone.effect_enabled = lambda: False
    phone.tap_text = lambda *a, **kw: None
    with pytest.raises(ControlError, match="bypass change failed readback"):
        phone.set_effect_enabled(172, True)


def test_pedal_preset_change_stops_chain_inspection_before_next_tap():
    phone = object.__new__(Phone)
    phone.header = lambda: {"slot": 172}
    phone.block_positions = lambda: [0.2, 0.5]
    visits = []
    taps = []

    def chain_view():
        visits.append(True)

    def verify_slot(slot):
        if len(visits) > 1:
            raise ControlError("Preset slot/name mismatch: refusing to edit")

    phone.chain_view = chain_view
    phone.verify_slot = verify_slot
    phone.tap = lambda *a: taps.append(a)
    phone.selected_amp = lambda: "Chromatic Pitch Shifter"
    with pytest.raises(ControlError, match="slot/name mismatch"):
        phone.read_chain()
    assert taps == [(0.2, 0.503)]


def test_save_navigation_never_substitutes_an_existing_preset(monkeypatch):
    phone = object.__new__(Phone)
    phone.texts = lambda: [
        Text("Preset Name", 0.2, 0.06, 1),
        Text("SAVE", 0.65, 0.935, 1),
        Text("CANCEL", 0.35, 0.935, 1),
        Text("171 Atom City Queen", 0.5, 0.7, 1),
    ]
    swipes = []
    phone.swipe = lambda *a: swipes.append(a)
    monkeypatch.setattr("mustang.phone.time.sleep", lambda *a: None)
    with pytest.raises(ControlError, match="bounded navigation"):
        phone.save_row(172)
    assert 0 < len(swipes) <= 12


def test_starred_current_slot_is_a_valid_save_target(monkeypatch):
    phone = object.__new__(Phone)
    current = Text("* 172 Empty", 0.5, 0.8, 1)
    phone.texts = lambda: [
        Text("Save Location in My Presets", 0.3, 0.16, 1),
        Text("SAVE", 0.65, 0.935, 1),
        Text("CANCEL", 0.35, 0.935, 1),
        current,
    ]
    phone.region_texts = lambda *a: [current]
    monkeypatch.setattr("mustang.phone.time.sleep", lambda *a: None)
    assert phone.save_row(172) is current


def test_closed_keyboard_never_sends_a_back_event():
    phone = object.__new__(Phone)
    calls = []
    phone.run = lambda *a: calls.append(a) or b"mInputShown=false"
    phone.tap = lambda *a: pytest.fail("Closed keyboard must not receive a dismissal tap")
    phone.hide_keyboard()
    assert calls == [("shell", "dumpsys", "input_method")]


def test_truncated_names_are_never_accepted_as_full_name_readback():
    assert Phone.name_matches("Atom City Queen AI", "Atom City Queen AI")
    assert Phone.name_matches("Atom City Queen Al", "Atom City Queen AI")
    assert not Phone.name_matches("Atom City ..n Al", "Atom City Queen AI")
    assert not Phone.name_matches("Atom City Queen", "Atom City Queen AI")


def test_native_catalog_rejects_zero_and_fractional_cent(tmp_path):
    from mustang.service import Service
    from mustang.store import Store

    service = Service(Store(tmp_path / "state.sqlite"))
    try:
        catalog = service.catalog()
        plan = TonePlan(
            name="Test", slot=172, chain=[Block(model="British 70s", kind="amp", parameters={"gain": 0})]
        )
        with pytest.raises(ValueError, match="out of range"):
            plan.validate_catalog(catalog)
        plan.chain[0].parameters = {"gain": 5.5}
        plan.chain.insert(
            0, Block(model="Chromatic Pitch Shifter", kind="effect", parameters={"pitch": 350.5})
        )
        with pytest.raises(ValueError, match="increments"):
            plan.validate_catalog(catalog)
    finally:
        service.pool.shutdown()


def test_duplicate_completed_capture_never_requests_new_playing(tmp_path):
    from mustang.service import Service
    from mustang.store import Store

    service = Service(Store(tmp_path / "state.sqlite"))
    try:
        s = service.create_session(SessionRequest())
        request = CaptureRequest(ready=True)
        import hashlib

        fingerprint = hashlib.sha256(request.model_dump_json().encode()).hexdigest()
        prior = service.store.put(
            "job",
            {
                "request_id": "capture-once",
                "session_id": s["id"],
                "action": "capture",
                "fingerprint": fingerprint,
                "status": "complete",
                "result": {"valid": True},
            },
        )
        service.update(s, status="complete")
        assert service.capture(s["id"], request, "capture-once")["id"] == prior["id"]
        with pytest.raises(ValueError, match="payload differs"):
            service.capture(s["id"], CaptureRequest(ready=True, seconds=20), "capture-once")
    finally:
        service.pool.shutdown()
