#!/usr/bin/env python3
"""Identifica qué cuenta CF corresponde a cada token. Mapa de cobertura de las 11."""
import json, subprocess
from collections import Counter
from pathlib import Path

HOME = Path("/data/data/com.termux/files/home")
SCAN = HOME / "miu/state/cf_scan.json"
OUT = HOME / "miu/state/cf_cobertura.json"

# Las 11 cuentas Gmail base (de cuentas_base)
CUENTAS_BASE = [
    "jhuarcaya938@gmail.com", "dieguito.vg16@gmail.com", "jaimepvicente@gmail.com",
    "franrussell81@gmail.com", "tabletonephantom@gmail.com", "dereckcito.vg16@gmail.com",
    "jaimepviccente@gmail.com", "javier19051997@gmail.com", "franchescopalacios9@gmail.com",
    "jaimedanielmartinez75@gmail.com", "cipher19051997@gmail.com",
]

def curl(url, tok, timeout=8):
    try:
        r = subprocess.run(["curl","-s","--max-time",str(timeout),
            "-H", f"Authorization: Bearer {tok}", url],
            capture_output=True, text=True, timeout=timeout+3)
        return json.loads(r.stdout) if r.stdout.strip() else {}
    except: return {}

def main():
    print("═══ COBERTURA CF — 11 CUENTAS ═══\n")
    if not SCAN.exists():
        print(f"❌ {SCAN} no existe")
        return

    scan = json.loads(SCAN.read_text())
    vivos = scan.get("vivos", [])
    print(f"Tokens vivos a identificar: {len(vivos)}\n")

    por_email = Counter()
    por_account = Counter()
    tokens_por_email = {}
    tokens_con_create = []

    for i, v in enumerate(vivos, 1):
        tok = v["token"]
        # Identificar usuario
        user = curl("https://api.cloudflare.com/client/v4/user", tok)
        email = None
        if user.get("success"):
            email = user.get("result", {}).get("email")

        # Identificar cuentas accesibles
        accounts = curl("https://api.cloudflare.com/client/v4/accounts?per_page=20", tok)
        account_ids = []
        if accounts.get("success"):
            account_ids = [a.get("id") for a in accounts.get("result", [])]

        # ¿Puede crear tokens?
        toks = curl("https://api.cloudflare.com/client/v4/user/tokens?per_page=1", tok)
        puede_crear = toks.get("success", False)

        if email:
            por_email[email] += 1
            tokens_por_email.setdefault(email, []).append({
                "sha": v.get("origen", "")[:30],
                "accounts": account_ids,
                "puede_crear": puede_crear,
            })
            if puede_crear:
                tokens_con_create.append(tok)

        for aid in account_ids:
            por_account[aid] += 1

        if i % 10 == 0:
            print(f"  {i}/{len(vivos)} procesados...")

    print()
    print(f"═══ EMAILS DETECTADOS EN TOKENS ({len(por_email)}) ═══")
    for email, count in por_email.most_common():
        marca = "✅" if email in CUENTAS_BASE else "⚠️ "
        print(f"  {marca} {email:40} {count} tokens")

    print()
    print(f"═══ COBERTURA DE LAS 11 CUENTAS BASE ═══")
    cubiertas = []
    faltantes = []
    for email in CUENTAS_BASE:
        if email in por_email:
            marca = "✅ CUBIERTA"
            cubiertas.append(email)
        else:
            marca = "❌ SIN TOKEN"
            faltantes.append(email)
        print(f"  {marca:14} {email}")

    print()
    print(f"Resumen cobertura: {len(cubiertas)}/{len(CUENTAS_BASE)}")
    if faltantes:
        print(f"\nCuentas sin token:")
        for f in faltantes:
            print(f"  - {f}")

    # Guardar
    resultado = {
        "emails_con_tokens": dict(por_email),
        "cuentas_base_cubiertas": cubiertas,
        "cuentas_base_faltantes": faltantes,
        "tokens_por_email": tokens_por_email,
        "tokens_con_create": len(tokens_con_create),
        "cobertura_pct": round(100 * len(cubiertas) / len(CUENTAS_BASE), 1),
    }
    OUT.write_text(json.dumps(resultado, indent=2, ensure_ascii=False))
    print(f"\n📄 {OUT}")

if __name__ == "__main__":
    main()
