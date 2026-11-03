#!/usr/bin/env python3
"""cf_topologia — inventario real de recursos CF por las 11 cuentas."""
import json, subprocess, time
from datetime import datetime, timezone
from pathlib import Path

HOME = Path("/data/data/com.termux/files/home")
SD = Path("/storage/25A9-180D/.miu-base")
OUT = HOME / "miu/state/cf_topologia.json"

def curl(url, tok, t=10):
    try:
        r = subprocess.run(["curl","-s","--max-time",str(t),
            "-H", f"Authorization: Bearer {tok}", url],
            capture_output=True, text=True, timeout=t+5)
        if r.returncode != 0: return None
        return json.loads(r.stdout) if r.stdout.strip() else None
    except: return None

def cargar():
    cuentas = {}
    map_file = SD / "cf_mapeo_11_cuentas.json"
    if map_file.exists():
        try: cuentas = json.loads(map_file.read_text()).get("cuentas", {})
        except: pass
    tokens = []
    tok_file = SD / "cf_tokens_todos.txt"
    if tok_file.exists():
        tokens = [t.strip() for t in tok_file.read_text().splitlines() if t.strip()]
    return cuentas, tokens

def inventariar(account_id, tokens):
    """Prueba los tokens hasta encontrar uno con acceso a esta cuenta."""
    for tok in tokens:
        # ¿este token ve esta cuenta?
        acc = curl(f"https://api.cloudflare.com/client/v4/accounts/{account_id}", tok, t=6)
        if not acc or not acc.get("success"):
            continue
        resultado = {"account_id": account_id, "token": tok[:16]+"...", "ok": True}
        # Workers
        w = curl(f"https://api.cloudflare.com/client/v4/accounts/{account_id}/workers/scripts", tok, t=10)
        resultado["workers"] = [s.get("id") for s in w.get("result", [])] if w and w.get("success") else []
        # KV
        kv = curl(f"https://api.cloudflare.com/client/v4/accounts/{account_id}/storage/kv/namespaces", tok, t=10)
        resultado["kv_namespaces"] = [{"id": n.get("id"), "title": n.get("title")} for n in kv.get("result", [])] if kv and kv.get("success") else []
        # D1
        d1 = curl(f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database", tok, t=10)
        resultado["d1_databases"] = [{"uuid": d.get("uuid"), "name": d.get("name")} for d in d1.get("result", [])] if d1 and d1.get("success") else []
        # R2
        r2 = curl(f"https://api.cloudflare.com/client/v4/accounts/{account_id}/r2/buckets", tok, t=10)
        resultado["r2_buckets"] = [b.get("name") for b in r2.get("result", {}).get("buckets", [])] if r2 and r2.get("success") else []
        return resultado
    return {"account_id": account_id, "ok": False, "error": "ningún token con acceso"}

def main():
    print("═══ TOPOLOGIA CF ═══\n")
    cuentas, tokens = cargar()
    print(f"Cuentas: {len(cuentas)} | Tokens: {len(tokens)}\n")
    if not cuentas or not tokens:
        print("❌ faltan cuentas o tokens")
        return

    resultado = {"schema": "cf-topologia-v1",
                 "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "accounts": []}

    total_w = total_kv = total_d1 = total_r2 = 0
    for email, aid in cuentas.items():
        print(f"── {email} ──")
        r = inventariar(aid, tokens)
        r["email"] = email
        resultado["accounts"].append(r)
        if r.get("ok"):
            n_w = len(r["workers"]); n_kv = len(r["kv_namespaces"])
            n_d1 = len(r["d1_databases"]); n_r2 = len(r["r2_buckets"])
            total_w += n_w; total_kv += n_kv; total_d1 += n_d1; total_r2 += n_r2
            print(f"  workers={n_w} kv={n_kv} d1={n_d1} r2={n_r2}")
            if r["workers"]: print(f"    workers: {', '.join(r['workers'][:5])}")
        else:
            print(f"  ❌ {r.get('error')}")
        time.sleep(0.3)

    resultado["totales"] = {"workers": total_w, "kv": total_kv,
                            "d1": total_d1, "r2": total_r2}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(resultado, indent=2, ensure_ascii=False))

    print(f"\n═══ TOTALES ═══")
    print(f"  Workers:      {total_w}")
    print(f"  KV:           {total_kv}")
    print(f"  D1:           {total_d1}")
    print(f"  R2:           {total_r2}")
    print(f"\n📄 {OUT}")

if __name__ == "__main__":
    main()
