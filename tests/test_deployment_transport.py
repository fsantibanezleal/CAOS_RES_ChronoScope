"""A transient server response may be retried; a broken deployment still fails."""
import importlib.util
from pathlib import Path
from urllib.error import HTTPError

import pytest

spec = importlib.util.spec_from_file_location(
    "deployment_transport", Path(__file__).resolve().parents[1] / "scripts/check_deployment.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
URL = "https://chronoscope.example/data/case.json"


class Response:
    url, status = URL, 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self):
        return b"exact response bytes"


def test_one_transient_response_is_recorded_before_exact_success(monkeypatch):
    responses = iter([HTTPError(URL, 503, "temporary", {}, None), Response()])
    calls, waits, log = [], [], []

    def opened(request, **kwargs):
        assert kwargs == {"timeout": 60}  # No TLS context or verification override.
        calls.append(request.full_url)
        result = next(responses)
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(module, "urlopen", opened)
    monkeypatch.setattr(module.time, "sleep", waits.append)
    assert module.fetch(URL, log) == (b"exact response bytes", URL, 200)
    assert calls == [URL, URL] and waits == [.5]
    assert log == [{"url": URL, "attempt": 1, "status": 503, "delay_seconds": .5}]


@pytest.mark.parametrize("code,headers,expected_calls", [
    (503, {}, 3), (404, {}, 1), (403, {}, 1),
    (429, {"Retry-After": "120"}, 1), (503, {"Retry-After": "not-a-delay"}, 1),
])
def test_adversarial_persistent_or_nonretryable_failure_is_never_admitted(monkeypatch, code, headers, expected_calls):
    calls, log = [], []

    def unavailable(request, **kwargs):
        calls.append(request.full_url)
        raise HTTPError(URL, code, "unavailable", headers, None)

    monkeypatch.setattr(module, "urlopen", unavailable)
    monkeypatch.setattr(module.time, "sleep", lambda _: None)
    with pytest.raises(HTTPError):
        module.fetch(URL, log)
    assert len(calls) == expected_calls
    assert len(log) == expected_calls - 1
