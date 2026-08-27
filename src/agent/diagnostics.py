"""
diagnostics.py — Health checks and network connectivity diagnostics for Losna CLI.

Provides lightweight, non-blocking diagnostic routines to check OpenRouter reachability,
distinguish between local network issues, OpenRouter gateway errors, and upstream model delays.
"""

import time
import requests
from typing import Dict, Any, Optional


def check_openrouter_health(api_key: str = "", timeout: float = 3.5) -> Dict[str, Any]:
    """
    Performs a lightweight, fast connectivity check to OpenRouter.

    Args:
        api_key (str): Optional OpenRouter API key. If provided, checks /auth/key endpoint;
                       otherwise checks the public /models endpoint.
        timeout (float): Request timeout in seconds. Default is 3.5s.

    Returns:
        dict with keys:
            - status (str): 'OK', 'AUTH_ERROR', 'GATEWAY_ERROR', 'RATE_LIMITED', 'TIMEOUT', 'NETWORK_ERROR'
            - reachable (bool): True if HTTP response was received from OpenRouter
            - latency_ms (float): Response roundtrip time in milliseconds
            - status_code (int or None): HTTP status code
            - message (str): Human-readable summary
            - details (str): Technical explanation
    """
    headers = {
        "User-Agent": "Losna-CLI-HealthCheck",
    }
    if api_key and api_key.strip():
        url = "https://openrouter.ai/api/v1/auth/key"
        headers["Authorization"] = f"Bearer {api_key.strip()}"
    else:
        url = "https://openrouter.ai/api/v1/models"

    t0 = time.time()
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        latency_ms = round((time.time() - t0) * 1000, 1)

        code = resp.status_code
        if code == 200:
            return {
                "status": "OK",
                "reachable": True,
                "latency_ms": latency_ms,
                "status_code": code,
                "message": f"OpenRouter API is reachable ({latency_ms}ms)",
                "details": "Gateway responded with HTTP 200 OK."
            }
        elif code in (401, 403):
            return {
                "status": "AUTH_ERROR",
                "reachable": True,
                "latency_ms": latency_ms,
                "status_code": code,
                "message": f"OpenRouter authentication failed (HTTP {code})",
                "details": "Invalid API key or insufficient permissions/credits."
            }
        elif code == 429:
            return {
                "status": "RATE_LIMITED",
                "reachable": True,
                "latency_ms": latency_ms,
                "status_code": code,
                "message": "OpenRouter rate limit exceeded (HTTP 429)",
                "details": "Too many requests or quota exhausted."
            }
        elif code >= 500:
            return {
                "status": "GATEWAY_ERROR",
                "reachable": True,
                "latency_ms": latency_ms,
                "status_code": code,
                "message": f"OpenRouter server error (HTTP {code})",
                "details": f"OpenRouter gateway returned error status {code}."
            }
        else:
            return {
                "status": "UNKNOWN",
                "reachable": True,
                "latency_ms": latency_ms,
                "status_code": code,
                "message": f"OpenRouter returned HTTP {code}",
                "details": resp.text[:200]
            }

    except requests.exceptions.Timeout:
        latency_ms = round((time.time() - t0) * 1000, 1)
        return {
            "status": "TIMEOUT",
            "reachable": False,
            "latency_ms": latency_ms,
            "status_code": None,
            "message": f"OpenRouter check timed out after {timeout}s",
            "details": "High network latency, packet loss, or server stall."
        }
    except requests.exceptions.ConnectionError as e:
        latency_ms = round((time.time() - t0) * 1000, 1)
        return {
            "status": "NETWORK_ERROR",
            "reachable": False,
            "latency_ms": latency_ms,
            "status_code": None,
            "message": "Unable to connect to OpenRouter",
            "details": f"Network/DNS error: {str(e)[:150]}"
        }
    except Exception as e:
        latency_ms = round((time.time() - t0) * 1000, 1)
        return {
            "status": "NETWORK_ERROR",
            "reachable": False,
            "latency_ms": latency_ms,
            "status_code": None,
            "message": "Unexpected error during health check",
            "details": str(e)[:150]
        }


def format_diagnostic_summary(diag: Dict[str, Any], model_name: str = "") -> str:
    """
    Formats the diagnostic result into a clear, colored user-facing string.

    Args:
        diag (dict): Diagnostic dictionary returned by check_openrouter_health.
        model_name (str): The model ID being called (e.g. 'deepseek/deepseek-v4-flash').

    Returns:
        str: Colorized explanation of the diagnosis.
    """
    GREEN = "\033[1;32m"
    YELLOW = "\033[1;33m"
    RED = "\033[1;31m"
    CYAN = "\033[1;36m"
    RESET = "\033[0m"

    status = diag.get("status", "")
    latency = diag.get("latency_ms", 0.0)
    model_str = f" for '{CYAN}{model_name}{RESET}'" if model_name else ""

    if status == "OK":
        return (
            f"  {GREEN}[Diagnostics]:{RESET} OpenRouter gateway is {GREEN}ONLINE{RESET} ({latency}ms latency).\n"
            f"  {YELLOW}ℹ{RESET} The delay{model_str} is likely due to high queue load, cold start, or slow Time-To-First-Token at the upstream model provider."
        )
    elif status == "AUTH_ERROR":
        return (
            f"  {RED}[Diagnostics]:{RESET} OpenRouter rejected authentication (HTTP {diag.get('status_code')}).\n"
            f"  {YELLOW}ℹ{RESET} Please verify your {CYAN}OPENROUTER_API_KEY{RESET} in ~/.losnarc or check your account credits at https://openrouter.ai/settings/keys."
        )
    elif status == "RATE_LIMITED":
        return (
            f"  {YELLOW}[Diagnostics]:{RESET} OpenRouter rate limit reached (HTTP 429).\n"
            f"  {YELLOW}ℹ{RESET} Please wait a moment before sending your next message."
        )
    elif status == "GATEWAY_ERROR":
        return (
            f"  {RED}[Diagnostics]:{RESET} OpenRouter gateway returned server error (HTTP {diag.get('status_code')}).\n"
            f"  {YELLOW}ℹ{RESET} OpenRouter or its upstream infrastructure may be experiencing a temporary outage."
        )
    elif status == "TIMEOUT":
        return (
            f"  {YELLOW}[Diagnostics]:{RESET} Connection to OpenRouter timed out ({latency}ms).\n"
            f"  {YELLOW}ℹ{RESET} Your internet connection or DNS to openrouter.ai may be slow or dropping packets."
        )
    else:
        return (
            f"  {RED}[Diagnostics]:{RESET} Cannot reach OpenRouter.\n"
            f"  {YELLOW}ℹ{RESET} Please check your local internet connection or proxy settings. ({diag.get('details', '')})"
        )
