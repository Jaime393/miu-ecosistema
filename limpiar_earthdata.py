#!/usr/bin/env python3
"""Limpia tokens Earthdata muertos y crea uno nuevo. Acepta API formats viejos y nuevos."""
import json, re, subprocess, time
from pathlib import Path

USER = "a36963"
PASS = "Anomalous363$$"
BASE = "https://urs.earthdata.nasa.gov/api/users"
OUT = Path("/storage/25A9-180D/.miu-base/earthdata_token.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

def curl(method, url, extra=None, timeout=15):
    cmd = ["curl", "-s", "--max-time", str(timeout), "-u", f"{USER}:{PASS}",
           "-H", "Accept: application/json"]
    if method != "GET":
        cmd.extend(["-X", method])
    if extra:
        cmd.extend(extra)
    cmd.append(url)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+5)
    return r.stdout.strip(), r.stderr.strip()

def probar_token(tok):
    """Prueba un token Earthdata contra un endpoint real de datos."""
    # Probar contra el endpoint de datos (más fiable que /tokens)
    r = subprocess.run([
        "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
        "--max-time", "10", "-H", f"Authorization: Bearer {tok}",
        "https://urs.earthdata.nasa.gov/api/users/tokens"
    ], capture_output=True, text=True, timeout=12)
    return r.stdout.strip() == "200"

def extraer_id(item):
    """Intenta sacar el ID de un token (en cualquier formato)."""
    if isinstance(item, dict):
        for key in ["token_id", "id", "jti", "access_token_id"]:
            if key in item: return item[key]
    if isinstance(item, str):
        # Decodificar JWT para ver si tiene un 'jti'
        try:
            parts = item.split(".")
            if len(parts) == 3:
                import base64
                b = parts[1] + "=" * (-len(parts[1]) % 4)
                payload = json.loads(base64.urlsafe_b64decode(b))
                return payload.get("jti") or payload.get("token_id")
        except: pass
    return None

def extraer_token(item):
    """Saca el token string de un item."""
    if isinstance(item, str): return item
    if isinstance(item, dict):
        for key in ["access_token", "token", "jwt"]:
            if key in item: return item[key]
    return None

def main():
    print("═══ LIMPIEZA EARTHDATA ═══\n")

    # 1. Listar
    print("Listando tokens...")
    raw, err = curl("GET", f"{BASE}/tokens")
    if err:
        print(f"  stderr: {err[:100]}")
    try:
        tokens = json.loads(raw)
    except:
        print(f"❌ no JSON: {raw[:200]}")
        return

    if not isinstance(tokens, list):
        print(f"❌ formato inesperado: {type(tokens).__name__} — {raw[:200]}")
        return

    print(f"Encontrados: {len(tokens)}\n")

    # 2. Probar cada uno (incluye soporte para strings y dicts)
    vivos, muertos = [], []
    for i, item in enumerate(tokens):
        tok = extraer_token(item)
        tid = extraer_id(item)
        if not tok:
            print(f"  [{i}] ❓ formato desconocido: {str(item)[:60]}")
            continue
        vivo = probar_token(tok)
        icon = "✅" if vivo else "❌"
        ident = tid or "(sin id)"
        print(f"  [{i}] {icon} {ident} {tok[:25]}...")
        entry = {"token": tok, "id": tid, "raw": item}
        if vivo:
            vivos.append(entry)
        else:
            muertos.append(entry)

    print(f"\nVivos: {len(vivos)} | Muertos: {len(muertos)}\n")

    # 3. Borrar muertos — probar ambos endpoints (revoke_token y DELETE)
    borrados = 0
    for m in muertos:
        tok = m["token"]
        tid = m.get("id")
        deleted = False

        # Intento 1: POST /api/users/revoke_token con token en body
        print(f"  Revocando {tok[:25]}...", end=" ", flush=True)
        data = f"token={tok}"
        r, e = curl("POST", f"{BASE}/revoke_token", extra=["-d", data])
        if r == "" or '"error"' not in r:
            print(f"✅ (POST revoke)")
            borrados += 1
            deleted = True
        else:
            # Intento 2: DELETE con token como path
            if tid:
                r2, _ = curl("DELETE", f"{BASE}/tokens/{tid}")
                if r2 == "" or '"error"' not in r2:
                    print(f"✅ (DELETE id)")
                    borrados += 1
                    deleted = True
            if not deleted:
                # Intento 3: DELETE con token como path
                r3, _ = curl("DELETE", f"{BASE}/tokens/{tok}")
                if r3 == "" or '"error"' not in r3:
                    print(f"✅ (DELETE tok)")
                    borrados += 1
                    deleted = True
                else:
                    print(f"❌ respuesta: {(r or r2 or r3)[:80]}")

        time.sleep(0.5)

    print(f"\nBorrados: {borrados}\n")

    # 4. Decidir payload
    if vivos:
        print(f"✅ {len(vivos)} token(s) vivos — usando el primero")
        payload = {"token": vivos[0]["token"], "user": USER,
                   "obtenido": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                   "fuente": "existente"}
    else:
        print("Creando token nuevo...")
        raw, _ = curl("POST", f"{BASE}/token")
        try:
            data = json.loads(raw)
        except:
            print(f"❌ no JSON: {raw[:200]}")
            return

        # Response puede ser: {"access_token":"..."} o {"token":"..."} o string directo
        if isinstance(data, str):
            token = data
        elif isinstance(data, dict):
            token = data.get("access_token") or data.get("token") or data.get("jwt")
        else:
            token = None

        if not token:
            print(f"❌ sin token en respuesta: {str(data)[:200]}")
            print("\n   Nota: probablemente los 2 tokens muertos siguen contando como slots.")
            print("   Solución: borrarlos manualmente en https://urs.earthdata.nasa.gov/profile")
            print("   → 'Delete Token' en cada uno")
            return

        print(f"✅ Nuevo: {token[:40]}...")
        payload = {"token": token, "user": USER,
                   "obtenido": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                   "fuente": "creado"}

    # 5. Guardar
    OUT.write_text(json.dumps(payload, indent=2))
    print(f"\n✅ Guardado: {OUT}")

if __name__ == "__main__":
    main()
