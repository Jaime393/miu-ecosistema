#!/usr/bin/env python3
"""Recupera JWT de Earthdata con las credenciales de a36963."""
import json, subprocess, time
from pathlib import Path

USER = "a36963"
PASS = "Anomalous363$$"
OUT = Path("/storage/25A9-180D/.miu-base/earthdata_token.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

def main():
    print(f"═══ RECUPERANDO EARTHDATA ({USER}) ═══\n")

    # Login → obtener JWT nuevo
    cmd = [
        "curl", "-s", "--max-time", "15",
        "-X", "POST", "https://urs.earthdata.nasa.gov/api/users/token",
        "-u", f"{USER}:{PASS}",
        "-H", "Accept: application/json"
    ]
    print("Solicitando token nuevo...")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)

    if r.returncode != 0:
        print(f"❌ curl falló: {r.stderr[:200]}")
        return

    try:
        data = json.loads(r.stdout)
    except:
        print(f"❌ respuesta no JSON: {r.stdout[:200]}")
        return

    token = data.get("access_token") or data.get("token") or data.get("jwt")
    if not token:
        print(f"❌ sin token en respuesta: {data}")
        return

    print(f"✅ JWT obtenido: {token[:40]}...")
    print(f"   longitud: {len(token)}")

    # Verificar que funciona
    print("\nVerificando contra API Earthdata...")
    test = subprocess.run([
        "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
        "--max-time", "10",
        "-H", f"Authorization: Bearer {token}",
        "https://urs.earthdata.nasa.gov/api/users/tokens"
    ], capture_output=True, text=True, timeout=12)

    code = test.stdout.strip()
    print(f"   HTTP {code}")
    if code == "200":
        print("   ✅ token vivo")
    else:
        print(f"   ⚠️  token responde {code} (puede ser válido igual)")

    # Guardar
    payload = {"token": token, "user": USER, "obtenido": time.strftime("%Y-%m-%dT%H:%M:%SZ")}
    OUT.write_text(json.dumps(payload, indent=2))
    print(f"\n✅ Guardado: {OUT}")

    # También añadir a .netrc (backup)
    netrc = Path("/data/data/com.termux/files/home/.netrc")
    if netrc.exists():
        backup = netrc.with_suffix(".netrc.bak_" + str(int(time.time())))
        backup.write_text(netrc.read_text())
        with netrc.open("a") as f:
            f.write(f"\nmachine urs.earthdata.nasa.gov login token password {token}\n")
        print(f"✅ Añadido a .netrc (backup: {backup.name})")

if __name__ == "__main__":
    main()
