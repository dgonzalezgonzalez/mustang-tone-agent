import threading

import pytest

from mustang.models import Block, CaptureRequest, SessionRequest, TonePlan
from mustang.phone import ControlError, Phone


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
