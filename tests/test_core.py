import threading
import time

import numpy as np
import pytest
from fastapi.testclient import TestClient

from mustang import audio
from mustang.api import create_app
from mustang.config import token
from mustang.models import Block, CaptureRequest, ModelSpec, ParameterSpec, SessionRequest, TonePlan
from mustang.service import Service
from mustang.store import Store


def catalog():
    return [
        ModelSpec(
            name="Studio Preamp",
            kind="amp",
            observed=True,
            parameters=[ParameterSpec(name="gain", unit="amp_scale", minimum=0, maximum=10)],
        )
    ]


def plan(gain=5):
    return TonePlan(
        name="Fresh tone",
        slot=172,
        chain=[Block(kind="amp", model="Studio Preamp", parameters={"gain": gain})],
    )


def wait_job(service, job):
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        value = service.store.get(job["id"])
        if value["status"] not in {"queued", "running"}:
            return value
        time.sleep(0.01)
    pytest.fail("Job failed to terminate")


@pytest.fixture
def service(tmp_path):
    instance = Service(Store(tmp_path / "test.sqlite"))
    instance.catalog = catalog
    yield instance
    instance.cancel.set()
    instance.pool.shutdown(wait=True)


def test_catalog_blocks_unverified_models_parameters_and_ranges():
    plan().validate_catalog(catalog())
    with pytest.raises(ValueError, match="out of range"):
        plan(11).validate_catalog(catalog())
    bad = plan()
    bad.chain[0].model = "Invented amp"
    with pytest.raises(ValueError, match="Unverified amp"):
        bad.validate_catalog(catalog())
    bad = plan()
    bad.chain[0].parameters["magic"] = 1
    with pytest.raises(ValueError, match="Unverified parameter"):
        bad.validate_catalog(catalog())


def test_audio_normalization_and_quality():
    rate = 48000
    t = np.arange(rate * 5) / rate
    guitar = 0.1 * np.sin(2 * np.pi * 220 * t)
    a = audio.features(guitar, rate)
    b = audio.features(guitar * 0.25, rate)
    assert audio.distance(a, b)["distance"] < 0.001
    assert "silence_or_too_quiet" in audio.features(np.zeros(rate * 5), rate)["issues"]
    assert "clipping" in audio.features(np.ones(rate * 5), rate)["issues"]
    with pytest.raises(ValueError, match="Invalid audio"):
        audio.distance(a, audio.features(np.zeros(rate * 5), rate))


def test_no_microphone_fallback(monkeypatch):
    monkeypatch.setattr(
        audio, "devices", lambda: [{"name": "Laptop microphone", "hostapi": "Windows WASAPI"}]
    )
    with pytest.raises(RuntimeError, match="No microphone fallback"):
        audio.fender_device()


def test_jobs_serialize_cancel_and_deduplicate(service):
    session = service.create_session(SessionRequest())
    started = threading.Event()

    def work(s, progress):
        started.set()
        service.cancel.wait(2)
        return {"finished": True}

    first = service.submit(session["id"], "test", work, request_id="one")
    started.wait(1)
    assert service.submit(session["id"], "test", work, request_id="one")["id"] == first["id"]
    with pytest.raises(ValueError, match="Another operation"):
        service.submit(session["id"], "other", work)
    service.stop()
    assert wait_job(service, first)["status"] == "cancelled"


def test_preserve_named_existing_preset(service):
    class ExistingPhone:
        def __init__(self, *args):
            pass

        def launch(self):
            pass

        def ensure_editor(self):
            pass

        def verify_slot(self, slot):
            return {"slot": slot, "name": "Atom City Queen"}

        def apply_plan(self, *args):
            pytest.fail("Existing preset must not be changed")

    service.phone_factory = ExistingPhone
    session = service.create_session(SessionRequest())
    result = wait_job(service, service.apply(session["id"], plan()))
    assert result["status"] == "failed"
    assert "existing presets are preserved" in result["message"]


def test_baseline_requirement_and_trial_limit(service):
    session = service.create_session(SessionRequest(max_trials=2))
    service.update(session, current_plan=plan().model_dump())
    with pytest.raises(ValueError, match="baseline"):
        service.capture(session["id"], CaptureRequest(role="trial", ready=True))
    service.update(session, baseline_ids=["a", "b"], trials=2)
    with pytest.raises(ValueError, match="trial limit"):
        service.capture(session["id"], CaptureRequest(role="trial", ready=True))
    with pytest.raises(ValueError, match="Refinement has stopped"):
        service.candidate(session["id"])


def test_new_candidates_require_baselines_and_fresh_playing(service):
    session = service.create_session(SessionRequest())
    service.update(session, current_plan=plan().model_dump(), status="awaiting_take")
    with pytest.raises(ValueError, match="two baseline takes"):
        service.apply(session["id"], plan(6))
    service.update(session, baseline_ids=["first", "second"])
    with pytest.raises(ValueError, match="fresh take"):
        service.apply(session["id"], plan(6))
    assert service.store.list("job") == []


def test_capture_needs_user_readiness(service):
    session = service.create_session(SessionRequest())
    with pytest.raises(ValueError, match="Press Ready"):
        service.capture(session["id"], CaptureRequest())


def test_authentication_origin_and_unknown_records(service):
    with TestClient(create_app(service)) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/api/state").status_code == 401
        headers = {"Authorization": f"Bearer {token()}"}
        assert client.get("/api/state", headers=headers).status_code == 200
        assert (
            client.get("/api/state", headers={**headers, "Origin": "https://evil.example"}).status_code == 403
        )
        assert client.get("/api/jobs/not-found", headers=headers).status_code == 404


def test_reference_permission_and_private_url(service):
    from mustang.models import ReferenceRequest
    from mustang.references import acquire, public_url

    with pytest.raises(ValueError, match="Confirm"):
        acquire(ReferenceRequest(url="https://example.com/a.wav", source="test"), None, threading.Event())
    with pytest.raises(ValueError, match="Private network"):
        public_url("https://127.0.0.1/file")
