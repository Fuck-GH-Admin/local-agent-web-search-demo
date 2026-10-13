import json

import pytest

from local_search_demo.config import DemoConfig
from local_search_demo.interfaces.cli import main, doctor


def test_doctor_never_logs_api_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-DO-NOT-PRINT")
    output = json.dumps(doctor())
    assert "test-secret-DO-NOT-PRINT" not in output
    assert doctor()["configuration"]["openai_key_configured"] is True


def test_invalid_api_mode(monkeypatch):
    monkeypatch.setenv("OPENAI_API_MODE", "unknown-mode")
    with pytest.raises(ValueError):
        DemoConfig.from_env()


def test_cli_doctor(capsys):
    assert main(["doctor"]) == 0
    body = json.loads(capsys.readouterr().out)
    assert body["phase"] == "B00"
    assert body["dependencies"]["httpx"]["status"] in {"installed", "missing"}


def test_cli_future_features_are_explicitly_unimplemented(capsys):
    assert main(["search", "test query"]) == 3
    body = json.loads(capsys.readouterr().out)
    assert body["status"] == "not_implemented"
