#!/usr/bin/env python3
"""
verificador_via_red — Termux consulta códigos de verificación que ya extrajo
el workflow de GitHub Actions desde Gmail vía Zapier.

Uso:
  python3 verificador_via_red.py           # ver últimos 20 códigos
  python3 verificador_via_red.py --wait 60 # esperar 60s por código de X servicio
  python3 verificador_via_red.py --servicio cloudflare
"""
import json, sys, time, subprocess
from datetime import datetime, timezone
from pathlib import Path

ANON = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRwZml5YnBndXV4c2tpdHN6aG1rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc3NjgyNTAsImV4cCI6MjEwMzM0NDI1MH0.W4V8xdyfZj6I7bj1VsfM5gjY17ZHPi8jhIJgDRpUYH0"
BASE = "https://tpfiybpguuxskitszhmk.supabase.co/rest/v1"

def curl_json(url):
    try:
        r = subprocess.run(
            ["curl", "-s", "--max-time", "8", url,
             "-H", f"apikey: {ANON}"],
            capture_output=True, text=True, timeout=10
        )
        if r.returncode == 0 and r.stdout.strip():
            return json.loads(r.stdout)
    except: pass
    return None

def listar_codigos(limit=20):
    data = curl_json(f"{BASE}/email_codes?order=ts.desc&limit={limit}")
    if not data:
        print("  ❌ Sin respuesta (¿tabla email_codes no existe?)")
        return []
    return data

def esperar_codigo(segundos=60, servicio=None):
    print(f"Esperando código de {servicio or 'cualquier servicio'} por {segundos}s...")
    inicio = time.time()
    vistos = set()
    while time.time() - inicio < segundos:
        codigos = listar_codigos(limit=5)
        for c in codigos:
            cid = c.get("id") or c.get("ts")
            if cid in vistos: continue
            vistos.add(cid)
            if servicio and servicio not in str(c).lower(): continue
            print(f"\n✅ CÓDIGO ENCONTRADO:")
            print(f"  {json.dumps(c, indent=2)}")
            return c
        time.sleep(10)
    print("⏱  Sin código en el tiempo esperado")
    return None

def main():
    if len(sys.argv) == 1:
        codigos = listar_codigos(20)
        print(f"═══ ÚLTIMOS {len(codigos)} CÓDIGOS EN LA RED ═══")
        for c in codigos:
            ts = c.get("ts") or c.get("created_at", "?")
            email = c.get("email", "?")
            codigo = c.get("codigo") or c.get("code", "?")
            servicio = c.get("servicio", "?")
            print(f"  [{ts}] {email} → {codigo} ({servicio})")
        return

    if "--wait" in sys.argv:
        idx = sys.argv.index("--wait")
        seg = int(sys.argv[idx+1]) if idx+1 < len(sys.argv) else 60
        serv = None
        if "--servicio" in sys.argv:
            s_idx = sys.argv.index("--servicio")
            if s_idx+1 < len(sys.argv):
                serv = sys.argv[s_idx+1]
        esperar_codigo(seg, serv)
        return

    if "--servicio" in sys.argv:
        idx = sys.argv.index("--servicio")
        serv = sys.argv[idx+1] if idx+1 < len(sys.argv) else None
        if serv:
            codigos = [c for c in listar_codigos(50)
                       if serv.lower() in str(c).lower()]
            print(f"Códigos de {serv}: {len(codigos)}")
            for c in codigos: print(f"  {json.dumps(c)}")

if __name__ == "__main__":
    main()
