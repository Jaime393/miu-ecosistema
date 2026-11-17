#!/usr/bin/env python3
"""Harvest existing public CF health routes. No keys, inference, or deployments."""
import argparse
import codecs
import concurrent.futures
from datetime import datetime, timezone
import json
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

REPO = "Jaime393/miu-ecosistema"
SOURCE = "data/auth/created_cf_workers_inventory.json"
KNOWN_DOMAIN = "jaimepvicente.workers.dev"


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def targets(inventory, limit):
    """Use only the account/domain association established in the project."""
    workers = inventory.get("jaimepvicente_account", {}).get("workers", [])
    seen = set()
    result = []
    for worker in workers:
        if not isinstance(worker, str) or not re.fullmatch(r"[a-z0-9-]{1,63}", worker):
            continue
        if worker in seen:
            continue
        seen.add(worker)
        result.append(f"https://{worker}.{KNOWN_DOMAIN}/health")
        if len(result) >= limit:
            break
    return result


def summarize(status, data):
    out = {"http": status, "health_verified": False, "inference_verified": False}
    if status != 200 or not isinstance(data, dict):
        out["state"] = "http_observed_not_health"
        return out
    out["health_verified"] = data.get("ok") is True
    out["state"] = "health_declared" if out["health_verified"] else "json_observed_not_health"
    # No response bodies, free text, prompts, credentials or model outputs retained.
    for key in ("version", "node", "nodeId", "motor"):
        value = data.get(key)
        if isinstance(value, str) and re.fullmatch(r"[\w./:@ -]{1,80}", value):
            out[key] = value
    return out


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        return None


def probe(url):
    result = {"url": url, "checked_at": utcnow(), "inference_verified": False}
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 MIU-resource-harvest"})
        opener = urllib.request.build_opener(NoRedirect)
        with opener.open(request, timeout=6) as response:
            raw = response.read(65537)
            result["http"] = response.status
            if len(raw) > 65536:
                result["state"] = "response_too_large"
            else:
                try:
                    result.update(summarize(response.status, json.loads(raw)))
                except (ValueError, UnicodeError):
                    result["state"] = "non_json_response"
    except urllib.error.HTTPError as error:
        result.update({"http": error.code, "health_verified": False,
                       "state": "protected" if error.code in (401, 403) else "http_error"})
    except Exception as error:
        result.update({"state": "probe_failed", "health_verified": False,
                       "error_class": type(error).__name__})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=12, choices=range(1, 97))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    reference = json.loads(subprocess.check_output(
        ["gh", "api", f"repos/{REPO}/commits/main", "--jq", "{sha:.sha}"]))
    source_sha = reference["sha"]
    encoded = subprocess.check_output(
        ["gh", "api", f"repos/{REPO}/contents/{SOURCE}?ref={source_sha}",
         "-H", "Accept: application/vnd.github.raw+json"], text=True)
    inventory = json.loads(codecs.decode(encoded, "rot_13"))
    urls = targets(inventory, args.limit)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(probe, urls))
    receipt = {
        "schema": "miu.public-cf-harvest/v1", "checked_at": utcnow(),
        "source": f"https://github.com/{REPO}/blob/{source_sha}/{SOURCE}",
        "source_sha": source_sha, "historical_inventory_total": inventory.get("total_workers"),
        "coverage": "known jaimepvicente domain only; other accounts not guessed",
        "probed": len(results),
        "health_declared": sum(r.get("health_verified", False) for r in results),
        "inference_verified": False, "credentials_used": False, "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in receipt.items() if k != "results"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
