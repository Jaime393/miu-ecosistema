#!/usr/bin/env python3
"""Verifica cobertura funcional: ¿los 55 tokens acceden a los 11 account_id de cuentas_base?"""
import json, subprocess
from pathlib import Path

HOME = Path("/data/data/com.termux/files/home")
SCAN = HOME / "miu/state/cf_scan.json"
OUT = HOME / "miu/state/cf_cobertura_accounts.json"

# Los 11 account_id de cuentas_base (los saco del dump previo)
ACCOUNTS_BASE = {
    "jhuarcaya938@gmail.com":       "cce82777c5814ee76c44fe1772c85465",
    "dieguito.vg16@gmail.com":      "308faedf16a56fbb68d464127c696844",
    "jaimepvicente@gmail.com":      "5ea7cd88010b382b154d2fcff00b9ab3",
    "franrussell81@gmail.com":      None,  # no visto en dump previo
    "tabletonephantom@gmail.com":   None,
    "dereckcito.vg16@gmail.com":    None,
    "jaimepviccente@gmail.com":     None,
    "javier19051997@gmail.com":     None,
    "franchescopalacios9@gmail.com":None,
    "jaimedanielmartinez75@gmail.com": None,
    "cipher19051997@gmail.com":     None,
}

def curl(url, tok, t=8):
    try:
        r = subprocess.run(["curl","-s","--max-time",str(t),
            "-H", f"Authorization: Bearer {tok}", url],
            capture_output=True, text=True, timeout=t+3)
        return json.loads(r.stdout) if r.stdout.strip() else {}
    except: return {}

def main():
    print("═══ COBERTURA FUNCIONAL CF ═══\n")
    scan = json.loads(SCAN.read_text())
    vivos = scan.get("vivos", [])
    print(f"Tokens a probar: {len(vivos)}\n")

    # Recolectar todos los account_id accesibles desde cualquier token
    accounts_visibles = {}  # account_id -> {name, emails_que_ven}
    procesados = 0

    for v in vivos:
        tok = v["token"]
        # User email
        u = curl("https://api.cloudflare.com/client/v4/user", tok)
        email = u.get("result", {}).get("email") if u.get("success") else None

        # Accounts
        a = curl("https://api.cloudflare.com/client/v4/accounts?per_page=50", tok)
        if a.get("success"):
            for acc in a.get("result", []):
                aid = acc.get("id")
                name = acc.get("name", "?")
                if aid not in accounts_visibles:
                    accounts_visibles[aid] = {"name": name, "emails": set()}
                if email:
                    accounts_visibles[aid]["emails"].add(email)

        procesados += 1
        if procesados % 10 == 0:
            print(f"  {procesados}/{len(vivos)} procesados, {len(accounts_visibles)} accounts visibles...")

    print(f"\n═══ ACCOUNTS CF VISIBLES DESDE LOS 55 TOKENS ═══")
    print(f"Total accounts accesibles: {len(accounts_visibles)}\n")

    for aid, info in accounts_visibles.items():
        emails = ", ".join(info["emails"])
        print(f"  {aid[:12]}... {info['name'][:30]:30} ({emails})")

    # Cruzar con cuentas_base
    print(f"\n═══ COBERTURA DE LAS 11 CUENTAS BASE ═══")
    cubiertas, faltantes = [], []
    for email, aid in ACCOUNTS_BASE.items():
        if aid and aid in accounts_visibles:
            print(f"  ✅ {email:40} account {aid[:12]}...")
            cubiertas.append(email)
        elif aid:
            print(f"  ❌ {email:40} account {aid[:12]}... NO accesible")
            faltantes.append(email)
        else:
            print(f"  ⚠️  {email:40} (account_id desconocido — no estaba en dump previo)")

    # Verificar si hay accounts_base cuya cuenta CF fue accedida pero con otro email
    print(f"\n═══ RESUMEN ═══")
    print(f"Cuentas base cubiertas: {len(cubiertas)}/{len([a for a in ACCOUNTS_BASE.values() if a])}")
    print(f"Accounts CF visibles totales: {len(accounts_visibles)}")

    out_data = {
        "accounts_visibles": {k: {"name": v["name"], "emails": list(v["emails"])}
                              for k, v in accounts_visibles.items()},
        "cuentas_base_cubiertas": cubiertas,
        "cuentas_base_faltantes": faltantes,
    }
    OUT.write_text(json.dumps(out_data, indent=2, ensure_ascii=False))
    print(f"\n📄 {OUT}")

if __name__ == "__main__":
    main()
