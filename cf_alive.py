#!/usr/bin/env python3
"""cf_alive — verifica qué workers únicos siguen vivos."""
import json, subprocess
from datetime import datetime, timezone
from pathlib import Path

HOME = Path("/data/data/com.termux/files/home")
TOPO = HOME / "miu/state/cf_topologia.json"
OUT = HOME / "miu/state/cf_alive.json"

CHECK = [
    "api-relay-v213", "corpus-api-miu", "fran-oraculo-miu",
    "miu-alpha-cf5", "miu-auto-franrussell81", "miu-autonomo-v92",
    "miu-beacon-6915f743-v224", "miu-beacon-f9a24523-v224",
    "miu-beacon-d0b37632-v224", "miu-beacon-franrussell81-v1",
    "miu-beacon-ba3dcff0-v224",
    "fran-proxy-micelio-v203-1", "fran-proxy-micelio-v203-16",
    "fran-colmena-1elttar-73",
    "fran-micelio-308f-cipher19051997-60",
    "fran-micelio-0b12-cipher19051997-81",
]

def curl_code(url, t=8):
    try:
        r = subprocess.run(["curl","-s","-o","/dev/null","-w","%{http_code}",
            "--max-time",str(t), url], capture_output=True, text=True, timeout=t+3)
        return int(r.stdout.strip() or 0)
    except: return 0

def main():
    print("═══ CF ALIVE ═══\n")
    topo = json.loads(TOPO.read_text())
    tok_file = Path("/storage/25A9-180D/.miu-base/cf_tokens_todos.txt")
    tokens = [t.strip() for t in tok_file.read_text().splitlines() if t.strip()]

    print("Subdomains por cuenta...")
    subs = {}
    for acc in topo.get("accounts", []):
        aid = acc.get("account_id")
        for tok in tokens:
            try:
                r = subprocess.run(["curl","-s","--max-time","8",
                    "-H", f"Authorization: Bearer {tok}",
                    f"https://api.cloudflare.com/client/v4/accounts/{aid}/workers/subdomain"],
                    capture_output=True, text=True, timeout=10)
                d = json.loads(r.stdout)
                if d.get("success"):
                    subs[aid] = d["result"].get("subdomain")
                    break
            except: pass
    for aid, s in subs.items():
        print(f"  {aid[:12]}: {s}")

    worker_to_account = {}
    for acc in topo.get("accounts", []):
        for w in acc.get("workers", []):
            worker_to_account[w] = acc.get("account_id")

    print(f"\nProbando {len(CHECK)} workers...\n")
    resultados = []
    for name in CHECK:
        aid = worker_to_account.get(name)
        sub = subs.get(aid) if aid else None
        if not sub:
            print(f"  ❓ {name}: sin subdomain")
            continue
        url = f"https://{name}.{sub}.workers.dev"
        code = curl_code(url)
        icon = "✅" if code in (200,301,302) else ("⚠️" if code in (401,403,404) else "❌")
        print(f"  {icon} {name:42} HTTP {code:3}")
        resultados.append({"name": name, "url": url, "http": code})

    OUT.write_text(json.dumps({"schema":"cf-alive-v1",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "resultados": resultados}, indent=2))
    print(f"\n📄 {OUT}")

if __name__ == "__main__":
    main()
