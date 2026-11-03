#!/usr/bin/env python3
"""termux_heartbeat — publica estado real de Termux a Panteón gossip_log."""
import json, re, subprocess
from datetime import datetime, timezone
from pathlib import Path

HOME = Path("/data/data/com.termux/files/home")
SD = Path("/storage/25A9-180D")
NUT = HOME / "miu/state"
ANON = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRwZml5YnBndXV4c2tpdHN6aG1rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc3NjgyNTAsImV4cCI6MjEwMzM0NDI1MH0.W4V8xdyfZj6I7bj1VsfM5gjY17ZHPi8jhIJgDRpUYH0"
BASE = "https://tpfiybpguuxskitszhmk.supabase.co/rest/v1/gossip_log"

def code(url, t=6):
    try:
        r = subprocess.run(["curl","-s","-o","/dev/null","-w","%{http_code}",
            "--max-time",str(t), url], capture_output=True, text=True, timeout=t+3)
        return int(r.stdout.strip() or 0)
    except: return 0

def main():
    pool = json.loads((NUT/"pool_credenciales.json").read_text()) if (NUT/"pool_credenciales.json").exists() else {}
    servicios = pool.get("servicios", {})

    tunnel = ""
    for f in [HOME/"miu-ecosistema/.state/tunnel_stable.txt", HOME/"miu-ecosistema/.state/tunnel_url.txt"]:
        if f.exists(): tunnel = f.read_text().strip(); break
    tunnel_ok = code(f"{tunnel}/health") if tunnel else 0

    # Buscar módulos en las 2 rutas posibles
    modulos = 0
    for d in [
        SD/"biblioteca_miu/todo/miu-ecosistema/modulos/flex",
        SD/"miu-brain-backup/miu-ecosistema/modulos/flex",
        HOME/"miu-ecosistema/modulos/flex",
    ]:
        if d.exists(): modulos += len(list(d.glob("*.py")))

    tg = SD/".miu-base/tg_bots_vivos.json"
    bots = len(set(re.findall(r"\d{9,12}:[A-Za-z0-9_-]{35,}", tg.read_text(errors="ignore")))) if tg.exists() else 0

    mesh_code = code("https://script.google.com/macros/s/AKfycbywWkuw8Dx_tuS6wIufgbmHi00lLgQ5TIFBQOp7U--6EDzlWSz693P_ulPuflVKorI/exec?token=MIU_5F8A6A80DFFE1701&action=ping", t=10)

    estado = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "local_ok": True,
        "tunnel": tunnel,
        "tunnel_ok": tunnel_ok == 200,
        "bots_count": bots,
        "modulos": modulos,
        "pool_servicios": len(servicios),
        "pool_con_vivos": sum(1 for s in servicios.values() if s.get("vivos",0) > 0),
        "pool_failover": pool.get("resumen", {}).get("servicios_con_failover", 0),
        "mesh_http": mesh_code,
        "mesh_ok": mesh_code in (200, 302),
        "phi": None,
        "phi_fuente": "sin_medidor_local",
    }
    # Leer estado real del enjambre (contexto-global es el único con datos medidos)
    try:
        r = subprocess.run([
            "curl","-s","--max-time","8",
            "https://tpfiybpguuxskitszhmk.supabase.co/functions/v1/contexto-global",
            "-H", f"Authorization: Bearer {ANON}",
            "-H", f"apikey: {ANON}",
        ], capture_output=True, text=True, timeout=12)
        red = json.loads(r.stdout)
        (NUT / "contexto_red.json").write_text(json.dumps(red, indent=2))
        vitales = red.get("vitales", {})
        estado["phi_enjambre"] = vitales.get("phi")
        estado["rho_enjambre"] = vitales.get("rho")
        estado["savia_enjambre"] = vitales.get("savia")
        estado["ciclo_enjambre"] = vitales.get("ciclo")
        estado["avisos_red"] = [
            red.get("make",{}).get("nota"),
            red.get("cloudflare",{}).get("nota"),
            red.get("llm",{}).get("nota"),
        ]
    except Exception:
        pass

    payload = {
        "origen": "termux-v270",
        "destino": "enjambre",
        "tipo": "termux_heartbeat",
        "payload": estado,
        "source_node": "termux-v270",
        "evidence_level": "measured",
    }
    subprocess.run([
        "curl","-s","-X","POST", BASE,
        "-H", f"apikey: {ANON}",
        "-H", f"Authorization: Bearer {ANON}",
        "-H", "Content-Type: application/json",
        
        "-d", json.dumps(payload),
    ], capture_output=True, timeout=35)

if __name__ == "__main__":
    main()
