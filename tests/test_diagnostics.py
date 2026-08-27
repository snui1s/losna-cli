import pytest
from unittest.mock import patch, MagicMock
import requests
from src.agent.diagnostics import check_openrouter_health, format_diagnostic_summary


def test_check_openrouter_health_200_ok():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    with patch("requests.get", return_value=mock_resp) as mock_get:
        res = check_openrouter_health(api_key="sk-test-key", timeout=2.0)
        assert res["status"] == "OK"
        assert res["reachable"] is True
        assert res["status_code"] == 200
        assert "latency_ms" in res
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert args[0] == "https://openrouter.ai/api/v1/auth/key"
        assert kwargs["headers"]["Authorization"] == "Bearer sk-test-key"


def test_check_openrouter_health_no_key_models_endpoint():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    with patch("requests.get", return_value=mock_resp) as mock_get:
        res = check_openrouter_health(api_key="", timeout=2.0)
        assert res["status"] == "OK"
        assert res["reachable"] is True
        args, kwargs = mock_get.call_args
        assert args[0] == "https://openrouter.ai/api/v1/models"


def test_check_openrouter_health_auth_error():
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    with patch("requests.get", return_value=mock_resp):
        res = check_openrouter_health(api_key="sk-invalid", timeout=2.0)
        assert res["status"] == "AUTH_ERROR"
        assert res["reachable"] is True
        assert res["status_code"] == 401


def test_check_openrouter_health_rate_limited():
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    with patch("requests.get", return_value=mock_resp):
        res = check_openrouter_health(api_key="sk-test", timeout=2.0)
        assert res["status"] == "RATE_LIMITED"
        assert res["reachable"] is True
        assert res["status_code"] == 429


def test_check_openrouter_health_gateway_error():
    mock_resp = MagicMock()
    mock_resp.status_code = 503
    with patch("requests.get", return_value=mock_resp):
        res = check_openrouter_health(api_key="sk-test", timeout=2.0)
        assert res["status"] == "GATEWAY_ERROR"
        assert res["reachable"] is True
        assert res["status_code"] == 503


def test_check_openrouter_health_timeout():
    with patch("requests.get", side_effect=requests.exceptions.Timeout("Timed out")):
        res = check_openrouter_health(api_key="sk-test", timeout=1.0)
        assert res["status"] == "TIMEOUT"
        assert res["reachable"] is False
        assert res["status_code"] is None


def test_check_openrouter_health_connection_error():
    with patch("requests.get", side_effect=requests.exceptions.ConnectionError("DNS failure")):
        res = check_openrouter_health(api_key="sk-test", timeout=1.0)
        assert res["status"] == "NETWORK_ERROR"
        assert res["reachable"] is False
        assert res["status_code"] is None


def test_format_diagnostic_summary():
    ok_diag = {"status": "OK", "latency_ms": 120.5, "status_code": 200}
    summary = format_diagnostic_summary(ok_diag, "deepseek/deepseek-v4-flash")
    assert "ONLINE" in summary
    assert "deepseek/deepseek-v4-flash" in summary

    auth_diag = {"status": "AUTH_ERROR", "status_code": 401}
    summary = format_diagnostic_summary(auth_diag)
    assert "authentication" in summary

    gateway_diag = {"status": "GATEWAY_ERROR", "status_code": 502}
    summary = format_diagnostic_summary(gateway_diag)
    assert "server error" in summary

    timeout_diag = {"status": "TIMEOUT", "latency_ms": 3500.0}
    summary = format_diagnostic_summary(timeout_diag)
    assert "timed out" in summary

    net_diag = {"status": "NETWORK_ERROR", "details": "Connection refused"}
    summary = format_diagnostic_summary(net_diag)
    assert "Cannot reach OpenRouter" in summary
