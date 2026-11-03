#!/usr/bin/env python3
"""browser_agent — controla Playwright (en proot) desde Termux.
Reusa lecto_gmail y pool_credenciales. Flujos como datos JSON."""
import json, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

HOME = Path("/data/data/com.termux/files/home")
STATE = HOME / "miu/state"
SESSIONS = Path("/storage/25A9-180D/.miu-base/browser_sessions")
FLUJOS = HOME / "miu-ecosistema/flujos"
SESSIONS.mkdir(parents=True, exist_ok=True)
FLUJOS.mkdir(parents=True, exist_ok=True)
STATE.mkdir(parents=True, exist_ok=True)

WORKER_IN_PROOT = "/root/browser_worker.py"

class Worker:
    def __init__(self, storage_path=None, storage_state_obj=None):
        self.proc = subprocess.Popen(
            ["proot-distro", "login", "ubuntu", "--", "python3", WORKER_IN_PROOT],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, bufsize=1
        )
        ready = self._read()
        if not ready or not ready.get("ready"):
            raise RuntimeError(f"worker no arrancó: {ready}")

        # Si storage_state_obj vino (cookies externas), escribirlo temporalmente
        if storage_state_obj:
            tmp = STATE / "_preload_storage.json"
            tmp.write_text(json.dumps(storage_state_obj))
            storage_path = str(tmp)

        self.send({"action": "init", "storage_path": storage_path, "headless": True})

    def _read(self):
        line = self.proc.stdout.readline()
        if not line: return None
        try: return json.loads(line)
        except: return {"raw": line}

    def send(self, cmd):
        self.proc.stdin.write(json.dumps(cmd) + "\n")
        self.proc.stdin.flush()
        return self._read()

    def close(self):
        try:
            self.send({"action": "quit_all"})
            self.proc.stdin.close()
            self.proc.wait(timeout=10)
        except: pass

def cargar_cookies_externas(nombre):
    """Carga storage_state. Primero busca en sessions (Playwright), luego en cookies.json (Chrome export)."""
    # Prioridad 1: sesión Playwright ya guardada (formato nativo)
    pl_session = Path("/storage/25A9-180D/.miu-base/browser_sessions") / f"{nombre}.json"
    if pl_session.exists():
        try:
            d = json.loads(pl_session.read_text())
            if isinstance(d, dict) and "cookies" in d:
                return d, None
        except: pass

    # Prioridad 2: export de Chrome
    src = STATE / f"{nombre}_cookies.json"
    if not src.exists():
        return None, f"no existe {src}"
    try:
        data = json.loads(src.read_text())
    except Exception as e:
        return None, f"json inválido: {e}"

    # Formato Playwright ya listo
    if isinstance(data, dict) and "cookies" in data and "origins" in data:
        return data, None

    # Formato Chrome: array de cookies (dentro de dict o directo)
    cookie_list = None
    if isinstance(data, list):
        cookie_list = data
    elif isinstance(data, dict) and isinstance(data.get("cookies"), list):
        cookie_list = data["cookies"]
    if cookie_list is not None:
        cookies = []
        for c in cookie_list:
            if not c.get("name") or not c.get("value"):
                continue
            # expiresDate (ms) o expirationDate (s) o expires (s)
            exp = c.get("expiresDate") or c.get("expirationDate") or c.get("expires", -1)
            try:
                exp = float(exp)
                if exp > 1e12:  # ms
                    exp = exp / 1000.0
            except:
                exp = -1
            same = c.get("sameSite", "Lax")
            if same not in ("Strict", "Lax", "None"):
                same = "Lax"
            cookies.append({
                "name": c["name"],
                "value": c["value"],
                "domain": c.get("domain", ""),
                "path": c.get("path", "/"),
                "expires": exp,
                "httpOnly": bool(c.get("httpOnly", False)),
                "secure": bool(c.get("secure", False)),
                "sameSite": same,
            })
        return {"cookies": cookies, "origins": []}, None

    return None, f"formato no reconocido (tipo: {type(data).__name__})"

def buscar_credencial(servicio, campo="email"):
    """Busca credencial del pool o all_credentials."""
    # Intentar pool primero
    pool = STATE / "pool_credenciales.json"
    if pool.exists():
        try:
            d = json.loads(pool.read_text())
            s = d.get("servicios", {}).get(servicio)
            if s and s.get("claves"):
                for c in s["claves"]:
                    if c.get("vivo"):
                        # El pool solo guarda sha, no valor. Ir a la fuente
                        break
        except: pass
    # Ir a all_credentials.json directo
    for p in [Path("/storage/25A9-180D/cognitive/all_credentials.json"),
              Path("/storage/25A9-180D/FranBot/cognitive/all_credentials.json")]:
        if not p.exists(): continue
        try:
            d = json.loads(p.read_text())
            for cred in d.get("credentials", []):
                if servicio.lower() in cred.get("service", "").lower():
                    if campo == "email" and cred.get("username"):
                        return cred["username"]
                    if campo == "password" and cred.get("password"):
                        return cred["password"]
        except: pass
    # Fallback: cuentas_gmail maestro
    if servicio in ("gmail", "google", "cloudflare"):
        return "jaimepvicente@gmail.com"
    return None

def leer_codigo_email(email, servicio, timeout=180):
    """Wrapper sobre lector_gmail."""
    try:
        sys.path.insert(0, str(HOME / "miu-ecosistema"))
        from lector_gmail import esperar_codigo
        r = esperar_codigo(email, filtro_asunto=servicio, timeout=timeout)
        if r.get("ok"): return r.get("codigo")
    except Exception as e:
        print(f"  ⚠️ lector_gmail: {e}", file=sys.stderr)
    return None

def reintentar_hasta_form(w, max_intentos=6, espera_entre=5):
    """Recarga hasta que aparezca form real o se pase turnstile.
    Devuelve (ok, detalles)."""
    detalles = []
    for intento in range(1, max_intentos + 1):
        # 1. ¿Turnstile visible? Intentar click
        r = w.send({"action": "click_turnstile"})
        if r and r.get("found") and r.get("passed"):
            print(f"  [{intento}] ✅ Turnstile pasado")
            detalles.append({"intento": intento, "turnstile": "passed"})
            return True, detalles
        if r and r.get("found"):
            print(f"  [{intento}] ⚠️  Turnstile clickeado, no pasó aún")

        # 2. ¿Hay form real?
        r = w.send({"action": "has_form"})
        if r and r.get("has_form"):
            print(f"  [{intento}] ✅ Form detectado (title: {r.get('title','')[:40]})")
            detalles.append({"intento": intento, "form": True, "title": r.get("title")})
            return True, detalles

        # 3. Recargar y reintentar
        print(f"  [{intento}] Sin form, recargando en {espera_entre}s...")
        time.sleep(espera_entre)
        w.send({"action": "reload"})
        time.sleep(2)

    return False, detalles

def ejecutar_flujo(nombre):
    """Ejecuta un flujo JSON. Devuelve resultado."""
    fpath = FLUJOS / f"{nombre}.json"
    if not fpath.exists():
        return {"ok": False, "error": f"flujo '{nombre}' no existe en {FLUJOS}"}

    flujo = json.loads(fpath.read_text())
    storage = SESSIONS / f"{flujo.get('session_key', nombre)}.json"

    print(f"═══ FLUJO: {flujo.get('nombre', nombre)} ═══")
    print(f"Session: {storage.name}")

    # Preload de cookies externas (Google, etc.)
    preload = flujo.get("preload_storage")
    state_obj = None
    if preload:
        state_obj, err = cargar_cookies_externas(preload)
        if err:
            print(f"⚠️  preload '{preload}': {err}")
        else:
            print(f"✅ preload '{preload}': {len(state_obj.get('cookies', []))} cookies cargadas")

    # storage_path SIEMPRE se pasa (exista o no) — para que save_session funcione
    state_obj = None
    storage_arg = str(storage)
    if storage.exists():
        print(f"Session: reusando {storage.name}")
    else:
        print(f"Session: nueva (se guardará en {storage.name})")

    print(f"Steps: {len(flujo.get('steps', []))}\n")

    w = Worker(storage_path=storage_arg, storage_state_obj=state_obj)
    resultado = {"flujo": nombre, "steps_ok": 0, "steps_fallidos": 0, "detalles": []}

    try:
        for i, step in enumerate(flujo.get("steps", []), 1):
            action = step["action"]
            print(f"[{i}] {action}", end=" ", flush=True)

            # Resolver credenciales
            if "credential" in step:
                val = buscar_credencial(flujo.get("servicio", ""), step["credential"])
                if not val:
                    print(f"❌ sin credencial '{step['credential']}'")
                    resultado["steps_fallidos"] += 1
                    break
                step["value"] = val

            # Esperar código de email (opcional si el servicio no pide 2FA)
            if action == "wait_email_code":
                if step.get("optional"):
                    # Esperar 30s máximo, si no llega, seguir
                    email = flujo.get("email") or buscar_credencial(flujo.get("servicio", ""), "email")
                    codigo = leer_codigo_email(email, step.get("servicio_filter", flujo.get("servicio", "")),
                                                step.get("timeout", 30)) if email else None
                    if codigo:
                        step["value"] = codigo
                        step["action"] = "fill"
                        print(f"→ código {codigo} ", end="")
                    else:
                        print("⏭ (sin 2FA, sigo)")
                        resultado["steps_ok"] += 1
                        continue
                else:
                    email = flujo.get("email") or buscar_credencial(flujo.get("servicio", ""), "email")
                    if not email:
                        print("❌ sin email")
                        resultado["steps_fallidos"] += 1
                        break
                    codigo = leer_codigo_email(email, step.get("servicio_filter", flujo.get("servicio", "")),
                                                step.get("timeout", 180))
                    if not codigo:
                        print(f"❌ timeout esperando código")
                        resultado["steps_fallidos"] += 1
                        break
                    step["value"] = codigo
                    step["action"] = "fill"
                    print(f"→ código {codigo} ", end="")

            # Ejecutar
            resp = w.send(step)
            if not resp or not resp.get("ok"):
                err = resp.get("error", "sin respuesta") if resp else "worker muerto"
                print(f"❌ {err[:80]}")
                resultado["steps_fallidos"] += 1
                resultado["detalles"].append({"step": i, "action": action, "error": err})
                break

            # Post-acción: en goto, reintentar hasta que aparezca form (o se pase Turnstile)
            if action == "goto":
                print(f"→ {resp.get('url','')[:60]}")
                ok, detalles_retry = reintentar_hasta_form(w, max_intentos=6, espera_entre=5)
                resultado["detalles"].append({"step": i, "retry": detalles_retry, "ok": ok})
                if not ok:
                    print(f"❌ No se pudo pasar a form tras 6 intentos")
                    resultado["steps_fallidos"] += 1
                    break
                print(f"✓ Página lista")
            elif action == "url":
                print(f"→ URL: {resp.get('url','?')}")
                print(f"  TITLE: {resp.get('title','?')[:60]}")
                resultado["url_final"] = resp.get("url", "")
                resultado["title_final"] = resp.get("title", "")
            else:
                print("✓")

            resultado["steps_ok"] += 1

        # Guardar sesión al final
        if resultado["steps_fallidos"] == 0:
            w.send({"action": "save_session"})
            print(f"\n✅ Sesión guardada: {storage}")
        else:
            print(f"\n⚠️  Steps fallidos — no se guarda sesión")

    finally:
        w.close()

    return resultado

def detectar_servicio(url):
    """Prueba una URL y reporta si es automatizable."""
    print(f"═══ DETECTAR: {url} ═══\n")
    w = Worker()
    try:
        w.send({"action": "goto", "url": url, "timeout": 30000})
        time.sleep(3)
        det = w.send({"action": "detect"}).get("detect", {})
        print(f"Title: {det.get('title', '?')}")
        print(f"URL: {det.get('url', '?')[:100]}")
        print(f"HTML len: {det.get('html_len', 0)}")
        print()
        if det.get("just_a_moment"):
            print("🔴 BLOQUEADO: Turnstile visible")
        elif det.get("turnstile") or det.get("challenge"):
            print("🟠 Turnstile invisible (puede pasar con fingerprint correcto)")
        elif det.get("captcha"):
            print("🔴 CAPTCHA presente")
        else:
            print("✅ POSIBLE: no hay bloqueo detectado")
        return det
    finally:
        w.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:")
        print("  browser_agent.py detectar <url>")
        print("  browser_agent.py flujo <nombre>")
        print(f"\nFlujos disponibles en: {FLUJOS}")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "detectar" and len(sys.argv) > 2:
        r = detectar_servicio(sys.argv[2])
        print(f"\n{json.dumps(r, indent=2)[:500]}")
    elif cmd == "flujo" and len(sys.argv) > 2:
        r = ejecutar_flujo(sys.argv[2])
        print(f"\n{json.dumps(r, indent=2)}")
        sys.exit(0 if r.get("steps_fallidos", 1) == 0 else 1)
    else:
        print(f"❌ comando desconocido: {cmd}")
