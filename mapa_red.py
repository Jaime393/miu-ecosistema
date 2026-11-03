#!/usr/bin/env python3
"""Mapa de red — qué responde y qué no. Guarda en SD."""
import json, subprocess
from datetime import datetime, timezone
from pathlib import Path

SD = Path("/storage/25A9-180D/.miu-base")

FUNCS = {
    "fepyzxwyneervidlybvi": [
        "miu-teclado-v153", "miu-corpus-v265", "miu-edge",
        "gossip-autonomo", "nutriente-total",
    ],
    "tpfiybpguuxskitszhmk": [
        "ai-relay-v225", "autonomo-claude", "beacon-deployer",
        "canal-dereckcito", "contexto-global", "corpus-sync",
        "github-bridge", "gossip-autonomo", "jardinero-autonomo",
        "mesh-autonomo", "nodo-integrador", "oracle-ask",
        "orquestador-maestro", "relay-health", "telegram-bridge",
    ],
    "fxmupxpwzzxnjcscpyuw": ["telegram-webhook"],
}

GAS = "https://script.google.com/macros/s/AKfycbywWkuw8Dx_tuS6wIufgbmHi00lLgQ5TIFBQOp7U--6EDzlWSz693P_ulPuflVKorI/exec"
TOKEN = "MIU_5F8A6A80DFFE1701"

def curl(url, t=8):
    timeout = t
    try:
        r = subprocess.run(["curl","-s","-o","/dev/null","-w","%{http_code}",
            "--max-time", str(timeout), url],
            capture_output=True, text=True, timeout=timeout+3)
        return int(r.stdout.strip() or 0)
    except: return 0

def main():
    print("═══ MAPA DE RED ═══\n")
    resultado = {"schema": "mapa-red-v1",
                 "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "gas_mesh": {}, "supabase": {}, "workers_cf": []}

    # GAS mesh
    print("── GAS mesh V153→V91 ──")
    gas_url = f"{GAS}?token={TOKEN}&action=ping"
    code = curl(gas_url)
    print(f"  HTTP {code}")
    resultado["gas_mesh"] = {"url": GAS, "http": code}

    # Supabase functions
    for proj, funcs in FUNCS.items():
        print(f"\n── Supabase {proj} ({len(funcs)}) ──")
        resultado["supabase"][proj] = {}
        for fn in funcs:
            url = f"https://{proj}.supabase.co/functions/v1/{fn}"
            code = curl(url)
            icon = "✅" if code in (200,405,401,403) else ("?" if code == 0 else "❌")
            print(f"  {icon} {fn:25} HTTP {code:3}")
            resultado["supabase"][proj][fn] = {"http": code}

    # Workers CF (los pocos que conocemos)
    print(f"\n── Workers CF vivos ──")
    for sub in ["jaimepvicente", "jhuarcaya938"]:
        for name in ["fran-oraculo-miu", "fran-proxy-micelio-v203-1", "api-relay-v213"]:
            url = f"https://{name}.{sub}.workers.dev"
            code = curl(url, t=6)
            icon = "✅" if code == 200 else ("?" if code == 0 else "❌")
            print(f"  {icon} {name:30}.{sub:15} HTTP {code}")
            resultado["workers_cf"].append({"url": url, "http": code})

    out = SD / "mapa_red.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(resultado, indent=2, ensure_ascii=False))
    print(f"\n📄 {out}")

if __name__ == "__main__":
    main()
