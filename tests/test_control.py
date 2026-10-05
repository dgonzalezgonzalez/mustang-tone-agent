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
