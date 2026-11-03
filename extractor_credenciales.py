#!/usr/bin/env python3
"""
Extractor de pares (email, password) reales. Solo Termux.
Fuentes: .netrc, bash_history, .env*, cuentas_unificadas, archivos de texto.
Verifica contra servicios reales. Guarda solo los VERIFICADOS.
"""
import json, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

HOME = Path("/data/data/com.termux/files/home")
OUT = HOME / "miu/state/cuentas_verificadas.json"
OUT.parent.mkdir(parents=True, exist_ok=True)

# Los 11 correos principales (los que funcionan en el ecosistema real)
PRINCIPALES = [
    # email, servicio_que_tiene_cuenta
    ("jaimepvicente@gmail.com", "cloudflare"),
    ("franrussell81@gmail.com", "cloudflare"),
    ("jaime393@gmail.com", "github"),
    ("6915f743@proton.me", "cloudflare"),
    ("ba3dcff0@proton.me", "cloudflare"),
    ("d0b37632@proton.me", "cloudflare"),
    ("f9a24523@proton.me", "cloudflare"),
    ("dieguito@proton.me", "cloudflare"),
    ("tabletonephantom@proton.me", "cloudflare"),
    ("jaime.p.viccente@gmail.com", "github"),
    ("anomalous363@proton.me", "generic"),
]

# Fuentes de texto libre
FUENTES = [
    HOME / ".netrc",
    HOME / ".git-credentials",
    HOME / ".bash_history",
    HOME / ".env.cf_auto",
    HOME / ".cloudflare.env",
    HOME / ".cloudflare_tokens.json",
    HOME / ".miu-panteon-env",
    HOME / ".miu/.env",
    HOME / "miu-ecosistema/.env",
    HOME / "miu-ecosistema/mesh.env",
    HOME / "miu-ecosistema/canonico.conf",
]

# Regex de email válido (TLD de 2+ letras, formato estándar)
EMAIL_RX = re.compile(r'\b[a-zA-Z0-9][a-zA-Z0-9._%+-]{1,40}@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b')

# Filtros de basura: descarta estos como password
BASURA = {
    'text', 'str', 'int', 'none', 'true', 'false', 'null', 'undefined',
    'en', 'es', 'us', 'the', 'and', 'or', 'not', 'string', 'object',
    'value', 'name', 'key', 'type', 'data', 'error', 'ok', 'info',
}

def es_password_valido(s):
    """8-64 chars, sin espacios, no es keyword, no es URL, no es email."""
    if not s or len(s) < 8 or len(s) > 64: return False
    if ' ' in s or '\t' in s or '\n' in s: return False
    if s.lower() in BASURA: return False
    if '://' in s or '@' in s or s.startswith(('http', 'www')): return False
    if s.isdigit() or s.isalpha() and len(s) < 12: return False
    # Al menos 2 categorías: minúscula, mayúscula, dígito, símbolo
    cats = sum([
        bool(re.search(r'[a-z]', s)),
        bool(re.search(r'[A-Z]', s)),
        bool(re.search(r'\d', s)),
        bool(re.search(r'[^a-zA-Z0-9]', s)),
    ])
    return cats >= 2

def extraer_candidatos(texto):
    """Busca (email, password) cerca en el texto."""
    pares = []
    lineas = texto.split('\n')
    for i, linea in enumerate(lineas):
        emails_aqui = EMAIL_RX.findall(linea)
        if not emails_aqui: continue
        # Buscar passwords en esta línea y las 3 siguientes
        contexto = '\n'.join(lineas[max(0,i-2):i+4])
        # Formatos comunes:
        # login: TOKEN  o  login TOKEN
        # machine host login X password Y
        # user=email password=X
        # email: X pass: Y
        tokens_ctx = re.findall(r'[A-Za-z0-9!@#$%^&*()_+\-=\[\]{}|;:,.<>?/~`]{8,64}', contexto)
        for email in emails_aqui:
            for tok in tokens_ctx:
                if tok == email: continue
                if tok in email or email in tok: continue
                if es_password_valido(tok):
                    pares.append((email, tok))
    return pares

def extraer_netrc(texto):
    """.netrc: machine HOST login USER password PASS"""
    pares = []
    for m in re.finditer(r'machine\s+\S+\s+login\s+(\S+)\s+password\s+(\S+)', texto):
        login, password = m.group(1), m.group(2)
        # Si login es email, usarlo
        if EMAIL_RX.match(login):
            pares.append((login, password))
        # Si login es token (hf_, ghp_), guardarlo aparte como token no password
    return pares

def verificar_cloudflare(email, password):
    """Intenta login en Cloudflare. Devuelve True si las credenciales son válidas."""
    # Cloudflare no tiene endpoint público de login. Usar el flujo real vía curl es frágil.
    # Mejor: intentar recuperar el token existente desde .env y verificar que pertenece a este email
    # Por ahora: no verificar Cloudflare directamente, solo marcar como "pendiente de verificación"
    return None  # None = desconocido

def verificar_github(email, password):
    """GitHub Basic Auth."""
    cmd = ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
           "--max-time", "8", "-u", f"{email}:{password}",
           "https://api.github.com/user"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return r.stdout.strip() == "200"
    except: return False

def verificar_huggingface(email, password):
    """HF login."""
    cmd = ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
           "--max-time", "8", "-u", f"{email}:{password}",
           "https://huggingface.co/api/whoami-v2"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return r.stdout.strip() == "200"
    except: return False

VERIFICADORES = {
    "github": verificar_github,
    "huggingface": verificar_huggingface,
    "cloudflare": verificar_cloudflare,  # no directo
}

def main():
    # 1. Extraer candidatos de todas las fuentes
    todos = {}
    for f in FUENTES:
        if not f.exists(): continue
        try: texto = f.read_text(errors="ignore")[:200000]
        except: continue
        # Pares por formato general
        for email, password in extraer_candidatos(texto):
            todos.setdefault(email, set()).add(password)
        # Pares por .netrc explícito
        if f.name == ".netrc":
            for email, password in extraer_netrc(texto):
                todos.setdefault(email, set()).add(password)

    # 2. Filtrar solo los 11 principales
    principales_set = {e.lower() for e, _ in PRINCIPALES}
    filtrados = {}
    for email, passwords in todos.items():
        if email.lower() in principales_set:
            filtrados[email] = passwords

    print(f"═══ EXTRACCIÓN ═══")
    print(f"Emails encontrados en fuentes: {len(todos)}")
    print(f"De los 11 principales, encontrados: {len(filtrados)}")
    print()

    for email, _ in PRINCIPALES:
        if email in filtrados:
            print(f"  ✓ {email}: {len(filtrados[email])} passwords candidatos")
        else:
            print(f"  ✗ {email}: sin password en fuentes")

    # 3. Verificar
    print()
    print("═══ VERIFICACIÓN ═══")
    verificados = {}
    pendientes = {}

    for email, servicio in PRINCIPALES:
        if email not in filtrados: continue
        verificador = VERIFICADORES.get(servicio)
        candidatos = filtrados[email]
        if not verificador:
            pendientes[email] = {"servicio": servicio, "passwords": list(candidatos),
                                 "razon": "sin verificador para este servicio"}
            continue
        for pwd in candidatos:
            print(f"  Probando {email} en {servicio}...", end=" ")
            ok = verificador(email, pwd)
            if ok is True:
                print("✓ VÁLIDO")
                verificados[email] = {"password": pwd, "servicio": servicio,
                                     "verificado": datetime.now(timezone.utc).isoformat()}
                break
            elif ok is False:
                print("✗")
            else:  # None
                print("? (sin verificación directa)")
                pendientes.setdefault(email, {"servicio": servicio,
                    "passwords": [], "razon": "servicio sin endpoint de verificación directa"})
                pendientes[email]["passwords"].append(pwd)
                break

    # 4. Guardar
    out = {
        "schema": "cuentas-verificadas-v1",
        "generado": datetime.now(timezone.utc).isoformat(),
        "verificadas": verificados,
        "pendientes": pendientes,
        "sin_password": [e for e, _ in PRINCIPALES if e not in filtrados],
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))

    print()
    print(f"═══ RESULTADO ═══")
    print(f"Verificadas con éxito: {len(verificados)}")
    print(f"Pendientes (sin verificación directa): {len(pendientes)}")
    print(f"Sin password encontrado: {len(out['sin_password'])}")
    print()
    print(f"Guardado: {OUT}")
    print()
    if verificados:
        print("Cuentas verificadas:")
        for email, info in verificados.items():
            print(f"  ✓ {email} → {info['servicio']}")

if __name__ == "__main__":
    main()
