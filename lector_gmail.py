#!/usr/bin/env python3
"""lector_gmail — lee códigos de verificación de Gmail vía IMAP.
11 cuentas base. Sin dependencias externas. Solo Python stdlib."""
import email, imaplib, json, re, sys, time
from email.header import decode_header
from pathlib import Path

CONF = Path("/storage/25A9-180D/.miu-base/cuentas_gmail.json")

def cargar():
    return json.loads(CONF.read_text())

def login(email_addr, app_pwd):
    """Conectar IMAP. Devuelve (mail, ok, error)."""
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        # Gmail app passwords: sin espacios
        mail.login(email_addr, app_pwd.replace(" ", ""))
        return mail, True, None
    except imaplib.IMAP4.error as e:
        return None, False, str(e)[:100]
    except Exception as e:
        return None, False, str(e)[:100]

def verificar_todas():
    """Prueba login de las 11 cuentas. Devuelve dict email -> {ok, error}."""
    conf = cargar()
    resultados = {}
    for em, pwd in conf["cuentas"].items():
        print(f"  Probando {em}...", end=" ", flush=True)
        mail, ok, err = login(em, pwd)
        if ok:
            print("✅")
            mail.logout()
            resultados[em] = {"ok": True, "error": None}
        else:
            print(f"❌ {err}")
            resultados[em] = {"ok": False, "error": err}
    return resultados

ASUNTOS_VERIFICACION = re.compile(
    r'(verif|c[oó]digo|code|confirm|reset|sign.?in|log.?in|'
    r'security|autentic|2fa|otp|passw|activ|bienven|welcome)',
    re.IGNORECASE
)
ASUNTOS_EXCLUIDOS = re.compile(
    r'(run failed|build|notification|github.com|deploy|workflow|'
    r'commit|pull request|issue|action|alert|digest|newsletter|unsubscribe)',
    re.IGNORECASE
)

def extraer_codigo(cuerpo, asunto=""):
    """Busca códigos SOLO en emails de verificación. Excluye builds/notifs."""
    # Si el asunto es de GitHub Actions o similares, ignorar
    if ASUNTOS_EXCLUIDOS.search(asunto):
        return None
    if "notifications@github.com" in asunto:
        return None
    if not ASUNTOS_VERIFICACION.search(asunto):
        return None

    # Patrones de código contextualizados (más específicos)
    patrones = [
        r'(?:code|c[oó]digo|verification|otp)\s*(?:is|:)?\s*[:\-]?\s*\b(\d{4,8})\b',
        r'\b(\d{6})\b',  # 6 dígitos aislados
        r'\b(\d{4,8})\b',  # fallback
    ]
    for pat in patrones:
        m = re.search(pat, cuerpo, re.IGNORECASE)
        if m:
            codigo = m.group(1)
            # Excluir años
            if codigo in ("2024", "2025", "2026", "2027"):
                continue
            return codigo

    # Links de verificación (último recurso)
    m = re.search(r'(https?://[^\s"<>]*(?:verif|confirm|reset|token|auth)[^\s"<>]*)', cuerpo)
    if m: return m.group(1)
    return None

def buscar_codigos(email_addr, app_pwd, segundos_ventana=600, filtro_asunto=None):
    """Busca códigos en correos recientes (últimos N segundos)."""
    mail, ok, err = login(email_addr, app_pwd)
    if not ok: return {"ok": False, "error": err}

    try:
        mail.select("INBOX")
        # Buscar correos recientes
        desde = (time.strftime("%d-%b-%Y", time.localtime(time.time() - 86400)))
        typ, data = mail.search(None, f'(SINCE {desde})')
        if typ != "OK":
            mail.logout()
            return {"ok": False, "error": "búsqueda falló"}

        ids = data[0].split()[-20:]  # últimos 20
        resultados = []
        ahora = time.time()

        for eid in reversed(ids):
            typ, msg_data = mail.fetch(eid, "(RFC822)")
            if typ != "OK": continue
            for part in msg_data:
                if not isinstance(part, tuple): continue
                msg = email.message_from_bytes(part[1])
                asunto_raw = msg.get("Subject", "")
                try:
                    asunto, enc = decode_header(asunto_raw)[0]
                    if isinstance(asunto, bytes):
                        asunto = asunto.decode(enc or "utf-8", errors="ignore")
                except: asunto = str(asunto_raw)

                if filtro_asunto and filtro_asunto.lower() not in asunto.lower():
                    continue

                # Fecha
                fecha_str = msg.get("Date", "")
                from email.utils import parsedate_to_datetime
                try:
                    fecha_ts = parsedate_to_datetime(fecha_str).timestamp()
                except:
                    fecha_ts = 0

                if ahora - fecha_ts > segundos_ventana: continue

                # Extraer cuerpo
                cuerpo = ""
                if msg.is_multipart():
                    for p in msg.walk():
                        if p.get_content_type() == "text/plain":
                            try: cuerpo = p.get_payload(decode=True).decode("utf-8", "ignore")
                            except: pass
                            if cuerpo: break
                else:
                    try: cuerpo = msg.get_payload(decode=True).decode("utf-8", "ignore")
                    except: pass

                codigo = extraer_codigo(cuerpo, asunto)
                if codigo:
                    resultados.append({
                        "asunto": asunto[:100],
                        "codigo": codigo,
                        "fecha": fecha_str[:40],
                        "de": msg.get("From", "")[:80],
                    })

        mail.logout()
        return {"ok": True, "cuenta": email_addr, "codigos": resultados[:10]}
    except Exception as e:
        try: mail.logout()
        except: pass
        return {"ok": False, "error": str(e)[:100]}

def esperar_codigo(email_addr, filtro_asunto=None, timeout=180, intervalo=15):
    """Espera activamente un código nuevo. Consulta cada `intervalo` seg."""
    conf = cargar()
    pwd = conf["cuentas"].get(email_addr)
    if not pwd:
        return {"ok": False, "error": f"cuenta {email_addr} no configurada"}

    inicio = time.time()
    vistos = set()
    while time.time() - inicio < timeout:
        r = buscar_codigos(email_addr, pwd, segundos_ventana=timeout+60, filtro_asunto=filtro_asunto)
        if r.get("ok"):
            for c in r.get("codigos", []):
                clave = (c["codigo"], c["fecha"])
                if clave not in vistos:
                    vistos.add(clave)
                    return {"ok": True, "cuenta": email_addr, "codigo": c["codigo"],
                            "asunto": c["asunto"], "fecha": c["fecha"], "de": c["de"]}
        time.sleep(intervalo)
    return {"ok": False, "error": f"timeout {timeout}s sin código"}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python3 lector_gmail.py verificar")
        print("  python3 lector_gmail.py codigos <email> [filtro_asunto] [ventana_seg]")
        print("  python3 lector_gmail.py esperar <email> [filtro_asunto] [timeout_seg]")
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "verificar":
        print("═══ VERIFICANDO 11 CUENTAS IMAP ═══\n")
        res = verificar_todas()
        ok = sum(1 for r in res.values() if r["ok"])
        print(f"\nResultado: {ok}/11 cuentas accesibles")
        # Guardar estado
        estado_file = Path("/storage/25A9-180D/.miu-base/estado_imap.json")
        estado_file.write_text(json.dumps({
            "verificado": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "ok": ok, "total": 11, "detalle": res,
        }, indent=2))
        print(f"Guardado: {estado_file}")

    elif cmd == "codigos":
        if len(sys.argv) < 3:
            print("Uso: codigos <email> [filtro_asunto] [ventana_seg]")
            sys.exit(1)
        email_addr = sys.argv[2]
        filtro = sys.argv[3] if len(sys.argv) > 3 else None
        ventana = int(sys.argv[4]) if len(sys.argv) > 4 else 600
        conf = cargar()
        pwd = conf["cuentas"].get(email_addr)
        if not pwd:
            print(f"❌ {email_addr} no está en la lista")
            sys.exit(1)
        r = buscar_codigos(email_addr, pwd, segundos_ventana=ventana, filtro_asunto=filtro)
        print(json.dumps(r, indent=2, ensure_ascii=False))

    elif cmd == "esperar":
        if len(sys.argv) < 3:
            print("Uso: esperar <email> [filtro_asunto] [timeout_seg]")
            sys.exit(1)
        email_addr = sys.argv[2]
        filtro = sys.argv[3] if len(sys.argv) > 3 else None
        timeout = int(sys.argv[4]) if len(sys.argv) > 4 else 180
        r = esperar_codigo(email_addr, filtro, timeout)
        print(json.dumps(r, indent=2, ensure_ascii=False))
