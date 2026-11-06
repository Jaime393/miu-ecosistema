#!/usr/bin/env python3
"""
ORQUESTADOR SUPREMO v3.0 — Merge del cruce (Termux)
Fusiona la estructura 3-fases de v2 (diagnostico -> sanacion -> estado)
con la supervision concreta del nodo actual (coordinator, pool, queue, AD/AE).
NO reinicia servicios (eso lo hace coordinator.sh) ni gestiona tuneles (pool).
Solo diagnostica, escribe un estado unificado y sana lo seguro e idempotente.
Uso: python3 orquestador_supremo_v3.py [--status] [--dry-run]
Corre cada minuto por cron (*/1); debe ser rapido (<15s) y ligero.
"""

import argparse
import json
import shutil
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
ECO = HOME / "miu-ecosistema"
STATE_DIR = ECO / ".state"
LOGS_DIR = ECO / "logs"
ORACULO_DIR = HOME / "oraculo"
REALIDAD = Path("/storage/25A9-180D/oraculo_miu/realidad.json")
VITALES = ECO / "data" / "vm_vitales.json"
QUEUE_DB = ORACULO_DIR / "queue.db"
STATUS_JSON = STATE_DIR / "orquestador_status.json"
AUDIT_LOG = LOGS_DIR / "supremo.log"
CARGO_SRC = HOME / ".cargo" / "registry" / "src"

for d in (STATE_DIR, LOGS_DIR):
    d.mkdir(parents=True, exist_ok=True)


def ts_now():
    return datetime.now(timezone.utc).isoformat()


def log_msg(msg):
    line = f"{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} {msg}"
    try:
        with open(AUDIT_LOG, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def curl_code(url, timeout=3):
    try:
        r = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
             "--max-time", str(timeout), url],
            capture_output=True, text=True, timeout=timeout + 5,
        )
        return int(r.stdout.strip() or 0)
    except Exception:
        return 0


def read_json(path):
    try:
        return json.loads(Path(path).read_text())
    except Exception:
        return None


def disk_pct():
    try:
        out = subprocess.run(["df", "/data"], capture_output=True,
                             text=True, timeout=5).stdout
        lines = out.strip().splitlines()
        if len(lines) >= 2:
            parts = lines[1].split()
            return int(parts[4].rstrip("%"))
    except Exception:
        pass
    return -1


def git_sync():
    try:
        def run(args):
            r = subprocess.run(["git", "-C", str(ECO)] + args,
                               capture_output=True, text=True, timeout=10)
            return r.stdout.strip()
        ahead = run(["rev-list", "--count", "@{u}..HEAD"])
        behind = run(["rev-list", "--count", "HEAD..@{u}"])
        dirty = run(["status", "--porcelain"])
        return (int(ahead or 0), int(behind or 0),
                len(dirty.splitlines()) if dirty else 0)
    except Exception:
        return (-1, -1, -1)


def fase1_diagnostico():
    d = {"timestamp": ts_now(), "servicios": {}, "tunel": {}, "cola": {},
         "disco_pct": -1, "realidad_edad_s": -1, "vitales_edad_s": -1,
         "git": {}, "salud": 100, "problemas": []}
    svc = {"oraculo_8771": "http://127.0.0.1:8771/health",
           "borde_8766": "http://127.0.0.1:8766/",
           "llama_8080": "http://127.0.0.1:8080/v1/models",
           "resil_8765": "http://127.0.0.1:8765/health"}
    for name, url in svc.items():
        code = curl_code(url, 3)
        d["servicios"][name] = code
        if code != 200:
            d["salud"] -= 20
            d["problemas"].append(f"{name}={code}")
    bore_url = ""
    try:
        bore_url = (STATE_DIR / "bore_url.txt").read_text().strip()
    except Exception:
        pass
    bore_health = curl_code(bore_url + "/health", 5) if bore_url else 0
    d["tunel"] = {"url": bore_url, "health": bore_health}
    if bore_health != 200:
        d["salud"] -= 15
        d["problemas"].append(f"bore={bore_health}")
    try:
        db = sqlite3.connect(f"file:{QUEUE_DB}?mode=ro", uri=True, timeout=5)
        rows = db.execute("SELECT estado, COUNT(*) FROM queue GROUP BY estado").fetchall()
        d["cola"] = {k: v for k, v in rows}
        n = db.execute(
            "SELECT COUNT(*) FROM queue WHERE estado='processing' "
            "AND datetime(ts_procesado) < datetime('now', '-10 minutes')"
        ).fetchone()[0]
        db.close()
        d["cola"]["atascadas"] = n
        if n > 0:
            d["salud"] -= 10
            d["problemas"].append(f"cola_atascadas={n}")
    except Exception:
        d["cola"] = {}
    pct = disk_pct()
    d["disco_pct"] = pct
    if pct >= 90:
        d["salud"] -= 15
        d["problemas"].append(f"disco={pct}%")
    real = read_json(REALIDAD)
    if real:
        try:
            obs = (real.get("observacion") or {}).get("observado_en") or real.get("observado_en")
            if obs:
                t = datetime.fromisoformat(str(obs).replace("Z", "+00:00"))
                age = (datetime.now(timezone.utc) - t).total_seconds()
                d["realidad_edad_s"] = int(age)
                if age > 600:
                    d["salud"] -= 10
                    d["problemas"].append(f"realidad_stale={int(age)}s")
        except Exception:
            pass
    else:
        d["problemas"].append("realidad_sin_archivo")
        d["salud"] -= 10
    vit = read_json(VITALES)
    if vit:
        try:
            t = datetime.fromisoformat(str(vit.get("ts", "")).replace("Z", "+00:00"))
            age = (datetime.now(timezone.utc) - t).total_seconds()
            d["vitales_edad_s"] = int(age)
            if age > 3600:
                d["salud"] -= 10
                d["problemas"].append(f"vitales_stale={int(age)}s")
        except Exception:
            pass
    else:
        d["problemas"].append("vitales_sin_archivo")
        d["salud"] -= 10
    ahead, behind, dirty = git_sync()
    d["git"] = {"ahead": ahead, "behind": behind, "dirty": dirty}
    if behind > 0:
        d["salud"] -= 5
        d["problemas"].append(f"git_behind={behind}")
    d["salud"] = max(0, min(100, d["salud"]))
    try:
        STATUS_JSON.write_text(json.dumps(d, indent=2, ensure_ascii=False))
    except Exception:
        pass
    return d


def fase2_sanacion(d):
    acciones = []
    if d.get("realidad_edad_s", -1) > 600 or "realidad_sin_archivo" in d.get("problemas", []):
        try:
            subprocess.run(["curl", "-s", "--max-time", "10",
                            "http://127.0.0.1:8771/estado", "-o", "/dev/null"], timeout=15)
            acciones.append("estado_refresh")
        except Exception:
            pass
    if d.get("disco_pct", 0) >= 90 and CARGO_SRC.exists():
        try:
            r = subprocess.run(["ps", "-A", "-o", "comm"], capture_output=True,
                               text=True, timeout=5)
            if "cargo" not in r.stdout.split():
                shutil.rmtree(CARGO_SRC, ignore_errors=True)
                acciones.append("cargo_src_podado")
        except Exception:
            pass
    return acciones


def main():
    ap = argparse.ArgumentParser(description="ORQUESTADOR SUPREMO v3.0 — merge del cruce")
    ap.add_argument("--status", action="store_true", help="Solo diagnostico, sin cambios")
    ap.add_argument("--dry-run", action="store_true", help="Diagnostico sin sanacion")
    args = ap.parse_args()
    d = fase1_diagnostico()
    if args.status:
        print(json.dumps(d, indent=2, ensure_ascii=False))
        return
    acciones = [] if args.dry_run else fase2_sanacion(d)
    resumen = (f"salud={d['salud']} svc={d['servicios']} bore={d['tunel'].get('health')} "
               f"cola={d['cola']} disco={d['disco_pct']}% real_edad={d['realidad_edad_s']}s "
               f"vit_edad={d['vitales_edad_s']}s git={d['git']} prob={d['problemas']} sana={acciones}")
    log_msg(resumen)


if __name__ == "__main__":
    main()
