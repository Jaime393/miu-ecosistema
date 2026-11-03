#!/usr/bin/env python3
"""evaluador_expiracion — solo reporta. NO renueva, NO modifica.
Regla: sumar siempre, reemplazar solo si confirmado muerto.
"""
import base64, json, re, subprocess, time
from datetime import datetime, timezone
from pathlib import Path

HOME = Path("/data/data/com.termux/files/home")
ESTADO = HOME / "miu/state/estado_local.json"
POOL = HOME / "miu/state/pool_credenciales.json"
OUT = HOME / "miu/state/evaluacion_expiracion.json"
OUT.parent.mkdir(parents=True, exist_ok=True)

def decodificar_jwt(token):
    """Devuelve payload o None si no es JWT."""
    try:
        partes = token.split(".")
        if len(partes) != 3: return None
        b = partes[1] + "=" * (-len(partes[1]) % 4)
        return json.loads(base64.urlsafe_b64decode(b))
    except: return None

def clasificar_token(token, servicio):
    """Devuelve dict con: expira (bool), dias_restantes (int|None), tipo."""
    info = {"expira": False, "dias_restantes": None, "tipo": "opaco"}

    # JWT (Supabase, Earthdata, Google OAuth)
    payload = decodificar_jwt(token)
    if payload and "exp" in payload:
        exp = payload["exp"]
        dias = int((exp - time.time()) / 86400)
        info["expira"] = True
        info["dias_restantes"] = dias
        info["tipo"] = "jwt"
        info["iss"] = payload.get("iss", "")[:40]
        return info

    # Tokens opacos: sin expiración conocida desde el token mismo
    # GitHub classic (ghp_): no expiran por defecto
    # HF: sí pueden expirar pero no se ve desde el token
    # CF API: no expiran, se revocan
    # Telegram: no expiran
    if token.startswith("ghp_"): info["tipo"] = "github-classic (no expira)"
    elif token.startswith("github_pat_"): info["tipo"] = "github-fine (puede expirar)"
    elif token.startswith("hf_"): info["tipo"] = "huggingface (expiración opcional)"
    elif token.startswith("gsk_"): info["tipo"] = "groq (no expira)"
    elif re.match(r'^\d{9,12}:[A-Za-z0-9_-]{35,}$', token): info["tipo"] = "telegram (no expira)"
    elif len(token) == 40 and "-" not in token and "_" not in token: info["tipo"] = "cloudflare (no expira)"

    return info

def main():
    # Leer tokens del estado local
    if not ESTADO.exists():
        print("❌ Ejecuta primero: python3 ~/miu-ecosistema/nucleo_local.py")
        return
    estado = json.loads(ESTADO.read_text())
    tokens_detalle = estado.get("tokens", {}).get("detalle", {})

    # Para cada token, necesitamos el valor real (no solo el hash)
    # Los valores están en los archivos originales, no en estado_local
    # Recargamos desde archivos
    from importlib.util import spec_from_file_location, module_from_spec
    spec = spec_from_file_location("nucleo", HOME/"miu-ecosistema/nucleo_local.py")
    nucleo = module_from_spec(spec)
    spec.loader.exec_module(nucleo)

    # Recarga con valores reales
    valores = {}
    for f in nucleo.FUENTES:
        if not f.exists(): continue
        try: texto = f.read_text(errors="ignore")[:100000]
        except: continue
        for servicio, patron in nucleo.PATRONES.items():
            for m in re.finditer(patron, texto):
                tok = m.group(0)
                if "://" in tok or "@" in tok or len(tok) < 20: continue
                h = nucleo.sha(tok)
                valores[h] = {"valor": tok, "servicio": servicio}

    # Evaluar
    evaluacion = {
        "schema": "evaluacion-expiracion-v1",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "regla": "SUMAR siempre. Reemplazar solo confirmados muertos o expirados <7d.",
        "renovar_urgente": [],   # exp < 0 o ya muerto
        "renovar_pronto": [],    # exp < 7d
        "sumar": [],             # servicio sin ningún vivo → buscar más
        "sin_info": [],          # tokens opacos, sin metadata de expiración
        "vivos": [],             # health check OK, sin urgencia
    }

    # Usar pool si existe
    pool = json.loads(POOL.read_text()) if POOL.exists() else None

    if pool:
        for servicio, info in pool.get("servicios", {}).items():
            vivas = [c for c in info.get("claves", []) if c.get("vivo")]
            muertas = [c for c in info.get("claves", []) if not c.get("vivo")]

            if not vivas:
                evaluacion["sumar"].append({
                    "servicio": servicio,
                    "razon": "0 tokens vivos — buscar/crear nuevos (no rotar)"
                })
                continue

            for c in vivas:
                sha_val = c.get("sha")
                val_info = valores.get(sha_val)
                if not val_info:
                    continue
                clas = clasificar_token(val_info["valor"], servicio)
                entry = {"servicio": servicio, "sha": sha_val, "tipo": clas["tipo"]}

                if clas["expira"] and clas["dias_restantes"] is not None:
                    entry["dias_restantes"] = clas["dias_restantes"]
                    if clas["dias_restantes"] <= 0:
                        entry["razon"] = "ya expirado"
                        evaluacion["renovar_urgente"].append(entry)
                    elif clas["dias_restantes"] < 7:
                        entry["razon"] = f"expira en {clas['dias_restantes']}d"
                        evaluacion["renovar_pronto"].append(entry)
                    else:
                        evaluacion["sin_info"].append(entry)  # expira pero falta
                else:
                    entry["razon"] = "sin fecha de expiración conocida"
                    evaluacion["sin_info"].append(entry)

    OUT.write_text(json.dumps(evaluacion, indent=2, ensure_ascii=False))

    # Reporte
    print(f"═══ EVALUACIÓN DE EXPIRACIÓN — {evaluacion['ts']} ═══")
    print(f"Regla: {evaluacion['regla']}\n")

    if evaluacion["renovar_urgente"]:
        print(f"🔴 RENOVAR YA ({len(evaluacion['renovar_urgente'])}) — expirados:")
        for e in evaluacion["renovar_urgente"]:
            print(f"   {e['servicio']:15} {e['sha']} — {e['razon']}")
        print()

    if evaluacion["renovar_pronto"]:
        print(f"🟠 RENOVAR PRONTO ({len(evaluacion['renovar_pronto'])}) — expiran <7d:")
        for e in evaluacion["renovar_pronto"]:
            print(f"   {e['servicio']:15} {e['sha']} — {e['razon']}")
        print()

    if evaluacion["sumar"]:
        print(f"➕ SUMAR ({len(evaluacion['sumar'])}) — servicios sin vivos:")
        for e in evaluacion["sumar"]:
            print(f"   {e['servicio']:15} — {e['razon']}")
        print()

    if evaluacion["sin_info"]:
        print(f"⚪ SIN INFO DE EXPIRACIÓN ({len(evaluacion['sin_info'])}) — tokens opacos:")
        for e in evaluacion["sin_info"][:10]:
            print(f"   {e['servicio']:15} {e['sha']} — {e['tipo']}")
        print()

    print(f"Guardado: {OUT}")

if __name__ == "__main__":
    main()
