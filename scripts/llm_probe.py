#!/usr/bin/env python3
"""Bounded catalog/auth probe for an explicitly identified provider; never infer quota."""
import argparse
import json
import os
from pathlib import Path
import urllib.error
import urllib.request
from datetime import datetime, timezone

PROVIDERS = {
    "google_ai_studio": ("https://generativelanguage.googleapis.com/v1beta/models", "x-goog-api-key"),
    "anthropic": ("https://api.anthropic.com/v1/models", "x-api-key"),
    "nvidia_nim": ("https://integrate.api.nvidia.com/v1/models", "Authorization"),
    "openrouter": ("https://openrouter.ai/api/v1/models", "Authorization"),
    "requesty": ("https://router.requesty.ai/v1/models", "Authorization"),
    "groq": ("https://api.groq.com/openai/v1/models", "Authorization"),
    "deepseek": ("https://api.deepseek.com/v1/models", "Authorization"),
    "together": ("https://api.together.xyz/v1/models", "Authorization"),
    "openai": ("https://api.openai.com/v1/models", "Authorization"),
}
UNAMBIGUOUS = {
    "sk-ant-": "anthropic", "nvapi-": "nvidia_nim", "sk-or-v1-": "openrouter",
    "rqsty-sk-": "requesty", "gsk_": "groq", "AQ.": "google_ai_studio",
    "AIza": "google_ai_studio",
}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        return None


def http_get(url, headers, timeout):
    request = urllib.request.Request(url, headers=headers)
    opener = urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(request, timeout=timeout) as response:
            raw = response.read(1048577)
            if len(raw) > 1048576:
                raise ValueError("response_too_large")
            return response.status, json.loads(raw)
    except urllib.error.HTTPError as error:
        return error.code, None


def catalog(data):
    if not isinstance(data, dict):
        return None
    rows = data.get("models", data.get("data"))
    if not isinstance(rows, list):
        return None
    names = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = row.get("id") or row.get("name")
        if isinstance(name, str) and 0 < len(name) <= 200:
            names.append(name)
    return names[:100]


def probe_key(key, provider=None, timeout=8, get=http_get):
    result = {"provider": provider if isinstance(provider, str) and provider in PROVIDERS else None,
              "valid": False, "auth_verified": False,
              "inference_verified": False, "quota_verified": False, "models": []}
    if not isinstance(key, str) or not key.strip():
        return dict(result, state="missing_key")
    if provider is None:
        provider = next((p for prefix, p in UNAMBIGUOUS.items() if key.startswith(prefix)), None)
    if not isinstance(provider, str) or provider not in PROVIDERS:
        return dict(result, state="provider_required")
    endpoint, header = PROVIDERS[provider]
    result.update(provider=provider, endpoint=endpoint)
    base_headers = {"User-Agent": "Mozilla/5.0 MIU-catalog-probe", "Accept": "application/json"}
    if provider == "anthropic":
        base_headers["anthropic-version"] = "2023-06-01"
    try:
        # A public catalog is capability discovery, never proof of a valid key.
        status, data = get(endpoint, dict(base_headers), timeout)
        result["control_http"] = status
        if status == 200:
            models = catalog(data)
            return dict(result, models=[m for m in (models or []) if key not in m],
                        state="public_catalog" if models is not None else "invalid_contract")
        if status not in (401, 403):
            return dict(result, state="control_rejected")
        headers = dict(base_headers)
        headers[header] = "Bearer " + key if header == "Authorization" else key
        status, data = get(endpoint, headers, timeout)
        models = catalog(data)
        result["auth_http"] = status
        if status == 200 and models is not None:
            return dict(result, models=[m for m in models if key not in m],
                        valid=True, auth_verified=True, state="authenticated_catalog")
        # Never try the same key at another provider, or rotate on quota failure.
        return dict(result, state="auth_rejected" if status in (401, 403)
                    else "quota_limited" if status == 429 else "invalid_contract")
    except Exception as error:
        return dict(result, state="probe_failed", error_class=type(error).__name__)


def probe_entries(entries, get=http_get):
    if not isinstance(entries, list) or len(entries) > 100:
        raise ValueError("expected_at_most_100_entries")
    results = []
    for index, entry in enumerate(entries):
        if isinstance(entry, str):
            key, provider = entry, None
        elif isinstance(entry, dict):
            key, provider = entry.get("key", entry.get("valor")), entry.get("provider")
        else:
            key, provider = None, None
        result = probe_key(key, provider, get=get)
        # Ordinals are local references. No key prefixes, aliases, raw values or errors.
        results.append(dict(result, ordinal=index))
    return {"schema": "miu.llm-auth-catalog-probe/v2",
            "ts": datetime.now(timezone.utc).isoformat(), "total": len(results),
            "validas": sum(r["auth_verified"] for r in results), "resultados": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-env", default="KEYS_INPUT")
    parser.add_argument("--output", type=Path, default=Path("observabilidad/key_registry.json"))
    args = parser.parse_args()
    try:
        entries = json.loads(os.environ.get(args.input_env) or "[]")
        receipt = probe_entries(entries)
    except Exception as error:
        print(json.dumps({"state": "invalid_input", "error_class": type(error).__name__}))
        raise SystemExit(2)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in receipt.items() if k != "resultados"}))


if __name__ == "__main__":
    main()
