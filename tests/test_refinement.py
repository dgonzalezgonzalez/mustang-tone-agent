import threading

import numpy as np
import pytest
import soundfile as sf
from test_core import plan, wait_job

from mustang import audio
from mustang.models import CaptureRequest, Feedback, SessionRequest
from mustang.service import Service
from mustang.store import Store


class FakePhone:
    def __init__(self, *args):
        pass

    def launch(self):
        pass

    def ensure_editor(self):
        pass

    def header(self):
        return {"slot": 172, "name": "Fresh tone"}

    def verify_slot(self, slot, expected_name=None):
        return {"slot": slot, "name": "Empty"}

    def verify_ble(self):
        return {"connected": True}

    def apply_plan(self, plan, previous=None):
        return {"verified": True}

    def save_reload(self, slot, name, expected=None):
        return {"verified": True, "saved": True, "reloaded": True}

    def restore(self, original, current):
        return {"verified": True}


@pytest.fixture
def service(tmp_path):
    s = Service(Store(tmp_path / "sessions.sqlite"), FakePhone)
    yield s
    s.pool.shutdown(wait=True)


def test_saved_preset_does_not_overwrite_session(service):
    s = service.create_session(SessionRequest())
    service.update(s, owned=True, current_plan=plan().model_dump())
    assert wait_job(service, service.save(s["id"]))["status"] == "complete"
    assert service.session(s["id"])["song"] == "Atom City Queen"
    assert service.store.list("preset")[0]["id"] != s["id"]


def test_save_retry_refuses_a_changed_parameter_before_writing(service):
    class ChangedPhone(FakePhone):
        saved = False

        def verify_plan(self, plan):
            raise RuntimeError("Saved parameter failed readback")

        def save_reload(self, *a, **kw):
            ChangedPhone.saved = True
            return super().save_reload(*a, **kw)

    service.phone_factory = ChangedPhone
    s = service.create_session(SessionRequest())
    service.update(s, owned=True, current_plan=plan().model_dump(), status="needs_attention")
    job = wait_job(service, service.save(s["id"]))
    assert job["status"] == "failed"
    assert not ChangedPhone.saved
    assert not service.store.list("preset")


def test_listening_acceptance_preserves_hardware_failure(service):
    s = service.create_session(SessionRequest())
    service.update(s, status="needs_attention")
    result = service.feedback(s["id"], Feedback(accepted=True))
    assert result["accepted"] is True
    assert result["status"] == "needs_attention"


def test_save_recovery_reopens_owned_slot_and_checks_name_before_writing(service):
    visits = []

    class RecoveryPhone(FakePhone):
        def header(self):
            return {"slot": 169, "name": "Other preset"}

        def back(self):
            visits.append("list")

        def open_slot(self, slot):
            visits.append(slot)

        def verify_slot(self, slot, expected_name=None):
            if expected_name:
                visits.append(expected_name)
            return {"slot": slot, "name": "Fresh tone"}

        def verify_plan(self, desired):
            visits.append("readback")

        def save_reload(self, *args, **kwargs):
            visits.append("save")
            return super().save_reload(*args, **kwargs)

    service.phone_factory = RecoveryPhone
    s = service.create_session(SessionRequest())
    service.update(s, owned=True, current_plan=plan().model_dump(), status="needs_attention", accepted=True)
    assert wait_job(service, service.save(s["id"]))["status"] == "complete"
    assert visits == ["list", 172, "Fresh tone", "readback", "save"]
    assert service.session(s["id"])["status"] == "complete"


def test_save_recovery_refuses_a_renamed_owned_slot(service):
    class RenamedPhone(FakePhone):
        def verify_slot(self, slot, expected_name=None):
            if expected_name:
                raise RuntimeError("Preset name mismatch: another song now owns this slot")
            return super().verify_slot(slot)

        def verify_plan(self, desired):
            pytest.fail("Do not inspect or save another song's settings")

        def save_reload(self, *args, **kwargs):
            pytest.fail("Do not overwrite another song")

    service.phone_factory = RenamedPhone
    s = service.create_session(SessionRequest())
    service.update(s, owned=True, current_plan=plan().model_dump(), status="needs_attention")
    result = wait_job(service, service.save(s["id"]))
    assert result["status"] == "failed"
    assert "another song" in result["message"]
    assert service.store.list("preset") == []


def test_best_candidate_retained_and_plateau_stops(service, monkeypatch):
    t = np.arange(240000) / 48000
    features = audio.features(0.1 * np.sin(2 * np.pi * 220 * t), 48000)
    s = service.create_session(SessionRequest())
    service.update(s, owned=True, current_plan=plan().model_dump())
    reference = service.store.put("audio", {"features": features, "path": "unused"})
    service.update(s, reference_id=reference["id"])
    monkeypatch.setattr(audio, "contamination", lambda *args: False)
    monkeypatch.setattr(audio, "record", lambda *args: {**features, "issues": []})
    for role in ("baseline", "baseline", "trial", "trial"):
        assert (
            wait_job(service, service.capture(s["id"], CaptureRequest(role=role, ready=True)))["status"]
            == "complete"
        )
    result = service.session(s["id"])
    assert result["status"] == "complete"
    assert result["trials"] == 2
    assert result["best_take"] == result["baseline_ids"][0]
    assert result["best_plan"] == plan().model_dump()


def test_invalid_takes_bounded_and_no_fake_comparison(service, monkeypatch):
    s = service.create_session(SessionRequest())
    service.update(s, current_plan=plan().model_dump())
    monkeypatch.setattr(audio, "record", lambda *args: {"valid": False, "issues": ["clipping"]})
    for _ in range(2):
        job = wait_job(service, service.capture(s["id"], CaptureRequest(ready=True)))
        assert job["result"]["valid"] is False
        assert "comparison" not in job["result"]
    assert service.session(s["id"])["status"] == "complete"
    with pytest.raises(ValueError, match="Apply a preset"):
        service.capture(s["id"], CaptureRequest(ready=True))


def test_reference_contamination_detects_exact_playback(tmp_path):
    rng = np.random.default_rng(2)
    reference = rng.normal(0, 0.1, 48000 * 8)
    a, b = tmp_path / "a.wav", tmp_path / "b.wav"
    sf.write(a, reference, 48000)
    sf.write(b, reference[48000 : 48000 * 6] * 0.4, 48000)
    assert audio.contamination(a, b)
    sf.write(b, rng.normal(0, 0.1, 48000 * 5), 48000)
    assert not audio.contamination(a, b)


def test_disconnect_and_restore_are_reported(service):
    s = service.create_session(SessionRequest())
    job = service.submit(
        s["id"], "disconnect", lambda *_: (_ for _ in ()).throw(ConnectionError("Disconnected"))
    )
    assert wait_job(service, job)["status"] == "failed"
    service.update(s, checkpoint="local", original={"slot": 172})
    assert wait_job(service, service.restore(s["id"]))["status"] == "complete"
    assert service.session(s["id"])["status"] == "restored"


def test_idempotency_conflict(service):
    s = service.create_session(SessionRequest())
    event = threading.Event()
    job = service.submit(s["id"], "test", lambda *_: event.wait(1), "key", "first")
    with pytest.raises(ValueError, match="payload differs"):
        service.submit(s["id"], "test", lambda *_: None, "key", "changed")
    event.set()
    assert wait_job(service, job)["status"] == "complete"


def test_worse_final_trial_restores_the_best_plan(service, monkeypatch):
    t = np.arange(240000) / 48000
    baseline = audio.features(0.1 * np.sin(2 * np.pi * 220 * t), 48000)
    worse = audio.features(0.1 * np.sin(2 * np.pi * 220 * t) + 0.03 * np.sin(2 * np.pi * 880 * t), 48000)
    outcomes = iter([baseline, baseline, worse, worse])
    monkeypatch.setattr(audio, "record", lambda *a: {**next(outcomes), "issues": []})
    monkeypatch.setattr(audio, "contamination", lambda *a: False)
    restored = []

    class TrackingPhone(FakePhone):
        def apply_plan(self, desired, previous=None):
            restored.append(desired.model_dump())
            return {"verified": True}

    service.phone_factory = TrackingPhone
    s = service.create_session(SessionRequest())
    service.update(s, current_plan=plan().model_dump(), owned=True)
    reference = service.store.put("audio", {"features": baseline, "path": "unused"})
    service.update(s, reference_id=reference["id"])
    for _ in range(2):
        assert wait_job(service, service.capture(s["id"], CaptureRequest(ready=True)))["status"] == "complete"
    service.update(s, current_plan=plan(gain=7).model_dump())
    for _ in range(2):
        assert (
            wait_job(service, service.capture(s["id"], CaptureRequest(role="trial", ready=True)))["status"]
            == "complete"
        )
    assert service.session(s["id"])["status"] == "complete"
    assert restored == [plan().model_dump()]
    assert service.session(s["id"])["current_plan"] == plan().model_dump()
