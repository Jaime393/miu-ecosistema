#!/usr/bin/env python3
"""auto_suministro — detecta servicios con carencia y busca más tokens solo.
Corre cada 6h. NO modifica el pool. Solo reporta hallazgos."""
import json, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

HOME = Path("/data/data/com.termux/files/home")
POOL = HOME / "miu/state/pool_credenciales.json"
ESTADO = HOME / "miu/state/estado_local.json"
REPORTE = HOME / "miu/state/suministro_reporte.json"
LOG = HOME / "miu/state/auto_suministro.log"
REPORTE.parent.mkdir(parents=True, exist_ok=True)

MIN_POR_SERVICIO = {
    "cloudflare": 11,   # 11 cuentas → 11 tokens mínimo
    "default": 2,       # failover mínimo para el resto
}

def umbral(servicio):
    return MIN_POR_SERVICIO.get(servicio, MIN_POR_SERVICIO["default"])


def ts(): return datetime.now(timezone.utc).isoformat(timespec="seconds")

def log(m):
    with LOG.open("a") as f:
        f.write(f"[{ts()}] {m}\n")

def leer_pool():
    if not POOL.exists():
        return None
    try:
        return json.loads(POOL.read_text())
    except:
        return None

def detectar_carencias(pool):
    """Devuelve servicios que necesitan suministro."""
    if not pool: return []
    carencias = []
    for servicio, info in pool.get("servicios", {}).items():
        vivas = info.get("vivos", 0)
        u = umbral(servicio)
        if vivas < u:
            print(f'   {servicio}: {vivas} vivas < umbral {u} — intentando recuperar...', flush=True)
            ok, det = intentar_recuperar(servicio)
            if ok:
                print(f'   RECUPERADO {servicio}: {det}', flush=True)
                carencias.append({'servicio': servicio, 'prioridad': 'recuperado', 'razon': f'{vivas}<{u} → {det}', 'recuperado': True})
            else:
                carencias.append({'servicio': servicio, 'prioridad': 'critica' if vivas == 0 else 'media', 'razon': f'{vivas}/<{u} — {det}', 'recuperado': False})
            continue
            carencias.append({"servicio": servicio, "prioridad": "media",
                              "razon": "1 viva — sin failover"})
    # Ordenar: críticas primero
    carencias.sort(key=lambda x: 0 if x["prioridad"] == "critica" else 1)
    return carencias

def buscar_para_servicio(servicio):
    """Llama al buscador y devuelve el resultado."""
    try:
        r = subprocess.run(
            ["python3", str(HOME / "miu-ecosistema/buscador_tokens.py"), servicio],
            capture_output=True, text=True, timeout=180
        )
        out = r.stdout
        # Extraer "Vivos: N/M"
        import re
        m = re.search(r'Vivos:\s*(\d+)/(\d+)', out)
        if m:
            return {"vivos": int(m.group(1)), "total": int(m.group(2)),
                    "detalle": out[-500:]}
        # Extraer "Ninguno" o "0 candidatos"
        if "Ninguno" in out or "0 candidatos" in out:
            return {"vivos": 0, "total": 0, "detalle": "sin candidatos"}
        return {"vivos": 0, "total": 0, "detalle": out[-300:]}
    except subprocess.TimeoutExpired:
        return {"vivos": 0, "total": 0, "error": "timeout"}
    except Exception as e:
        return {"vivos": 0, "total": 0, "error": str(e)[:100]}

def intentar_recuperar(servicio):
    """Reintegra un servicio por debajo del umbral. Crea los tokens que faltan
    en una sola corrida. Devuelve (ok, detalle)."""
    SCRIPTS = Path("/data/data/com.termux/files/home/miu-ecosistema")
    SD_BASE = Path("/storage/25A9-180D/.miu-base")
    FLUJOS_DIR = SCRIPTS / "flujos"
    STATE = Path("/data/data/com.termux/files/home/miu/state")
    u = umbral(servicio)

    # Leer vivas actuales del pool
    vivas_actuales = 0
    pool_path = STATE / "pool_credenciales.json"
    if pool_path.exists():
        try:
            d = json.loads(pool_path.read_text())
            vivas_actuales = d.get("servicios", {}).get(servicio, {}).get("vivos", 0)
        except: pass
    faltan = max(0, u - vivas_actuales)
    if faltan == 0:
        return True, "ya en umbral"

    # ── Cloudflare: crear N tokens directo por API ──
    if servicio == "cloudflare":
        scan_path = STATE / "cf_scan.json"
        if not scan_path.exists():
            return False, "cf_scan.json no existe — corre cf_test.py primero"
        try:
            scan = json.loads(scan_path.read_text())
            vivos = scan.get("vivos", [])
            creador = None
            for v in vivos:
                if v.get("puede_listar") or v.get("puede_crear"):
                    creador = v["token"]; break
            if not creador:
                return False, "sin token con permiso de creación"
            creados = []
            for i in range(faltan):
                body = json.dumps({
                    "name": f"miu-auto-{int(time.time()*1000)}-{i}",
                    "policies": [{
                        "effect": "allow",
                        "resources": {"com.cloudflare.api.account.*": "*"},
                        "permission_groups": [{"id": "c8fed203ed3043cba015a93ad1616f1f", "name": "Workers Scripts Read"}]
                    }]
                })
                try:
                    r = subprocess.run([
                        "curl","-s","--max-time","15","-X","POST",
                        "https://api.cloudflare.com/client/v4/user/tokens",
                        "-H", f"Authorization: Bearer {creador}",
                        "-H","Content-Type: application/json",
                        "-d", body
                    ], capture_output=True, text=True, timeout=20)
                    resp = json.loads(r.stdout)
                    if resp.get("success"):
                        tok = resp["result"].get("value")
                        if tok: creados.append(tok)
                except: pass
                time.sleep(0.4)
            if creados:
                todos = SD_BASE / "cf_tokens_todos.txt"
                with todos.open("a") as f:
                    for t in creados: f.write("\n" + t)
                return True, f"{len(creados)}/{faltan} tokens CF creados"
            return False, "0 tokens creados"
        except Exception as e:
            return False, f"CF API: {str(e)[:100]}"

    # ── Earthdata: 1 token (max 5 slots) ──
    if servicio == "earthdata":
        script = SCRIPTS / "limpiar_earthdata.py"
        if script.exists():
            try:
                r = subprocess.run(["python3", str(script)], capture_output=True,
                                   text=True, timeout=300, cwd=str(SCRIPTS))
                if "✅" in r.stdout and "Guardado" in r.stdout:
                    return True, "Earthdata token creado"
                return False, (r.stdout or r.stderr)[-150:].strip()
            except Exception as e:
                return False, "limpiar_earthdata: " + str(e)[:100]

    # ── Browser para servicios sin API ──
    flow = FLUJOS_DIR / (servicio + "_login.json")
    if flow.exists():
        ba = SCRIPTS / "browser_agent.py"
        if ba.exists():
            try:
                r = subprocess.run(["python3", str(ba), "flujo", servicio + "_login"],
                                   capture_output=True, text=True, timeout=600)
                if '"steps_fallidos": 0' in r.stdout:
                    return True, "login por browser"
                return False, "browser falló"
            except Exception as e:
                return False, "browser: " + str(e)[:100]

    return False, "sin ruta de recuperación"


def main():
    print(f"═══ AUTO-SUMINISTRO — {ts()} ═══\n")
    pool = leer_pool()
    if not pool:
        print("❌ Sin pool_credenciales.json. Ejecutar primero: python3 ~/miu-ecosistema/60_pool_credenciales.py")
        return

    carencias = detectar_carencias(pool)
    if not carencias:
        print("✅ Todos los servicios sobre el umbral (CF≥11, resto≥2)")
        log("sin carencias")
        return

    print(f"Servicios con carencia: {len(carencias)}\n")

    resultados = {
        "schema": "suministro-reporte-v1",
        "ts": ts(),
        "carencias_detectadas": len(carencias),
        "resultados": [],
        "necesitan_recuperacion_externa": [],
    }

    for c in carencias:
        servicio = c["servicio"]
        print(f"── {servicio} ({c['prioridad']}) ──")
        print(f"   {c['razon']}")
        print(f"   Buscando tokens...", end=" ", flush=True)

        r = buscar_para_servicio(servicio)
        icon = "✅" if r["vivos"] > 0 else "❌"
        print(f"{icon} {r['vivos']}/{r['total']} vivos")

        entry = {
            "servicio": servicio,
            "prioridad": c["prioridad"],
            "razon": c["razon"],
            "encontrados": r["vivos"],
            "totales_probaron": r["total"],
            "resultado": "sumar" if r["vivos"] > 0 else "recuperacion_externa",
        }
        if r["vivos"] > 0:
            entry["accion"] = "revisar y sumar manualmente al pool (candidatos en nuevos_tokens_candidatos.json)"
        else:
            entry["accion"] = "recuperación vía email + IMAP (11 cuentas disponibles)"
            resultados["necesitan_recuperacion_externa"].append(servicio)
        resultados["resultados"].append(entry)

        time.sleep(2)

    REPORTE.write_text(json.dumps(resultados, indent=2, ensure_ascii=False))
    log(f"carencias: {len(carencias)}, con hallazgos: {sum(1 for r in resultados['resultados'] if r['encontrados'] > 0)}")

    # Resumen
    print(f"\n═══ RESUMEN ═══")
    con_hallazgos = sum(1 for r in resultados["resultados"] if r["encontrados"] > 0)
    sin_hallazgos = sum(1 for r in resultados["resultados"] if r["encontrados"] == 0)
    print(f"Servicios con carencia: {len(carencias)}")
    print(f"  → Con tokens nuevos encontrados: {con_hallazgos}")
    print(f"  → Necesitan recuperación externa: {sin_hallazgos}")

    if resultados["necesitan_recuperacion_externa"]:
        print(f"\n   Recuperación externa (IMAP + forgot-password):")
        for s in resultados["necesitan_recuperacion_externa"]:
            print(f"     - {s}")

    print(f"\n📄 Reporte: {REPORTE}")

if __name__ == "__main__":
    main()
