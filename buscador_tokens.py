#!/usr/bin/env python3
"""buscador_tokens — busca tokens de un servicio en TODO el sistema.
Solo suma. Nunca reemplaza. Solo lectura."""
import json, re, subprocess, sys
from pathlib import Path

HOME = Path("/data/data/com.termux/files/home")
SD = Path("/storage/25A9-180D")

# Patrones específicos por servicio
PATRONES = {
    "earthdata": [r"eyJ0eXAiOiJKV1QiLCJvcmlnaW4iOiJFYXJ0aGRhdGE[A-Za-z0-9_\-\.]+"],
    "groq": [r"gsk_[A-Za-z0-9]{40,}"],
    "anthropic": [r"sk-ant-[A-Za-z0-9_\-]{40,}"],
    "deepseek": [r"sk-[a-f0-9]{32}"],
    "openai": [r"sk-proj-[A-Za-z0-9_\-]{40,}"],
    "github": [r"gh[pousr]_[A-Za-z0-9]{36,}", r"github_pat_[A-Za-z0-9_]{80,}"],
    "huggingface": [r"hf_[A-Za-z0-9]{30,}"],
    "cloudflare": [r"[A-Za-z0-9_\-]{40}"],
    "telegram": [r"\d{9,12}:[A-Za-z0-9_-]{35,}"],
}

# Endpoints de verificación
VERIFICAR = {
    "earthdata": {"url": "https://goldsmr4.gesdisc.eosdis.nasa.gov/data/MERRA2/",
                  "hdr": lambda k: {"Authorization": f"Bearer {k}"}, "ok": [200]},
    "groq": {"url": "https://api.groq.com/openai/v1/models",
             "hdr": lambda k: {"Authorization": f"Bearer {k}"}, "ok": [200, 429]},
    "anthropic": {"url": "https://api.anthropic.com/v1/models",
                  "hdr": lambda k: {"x-api-key": k, "anthropic-version": "2023-06-01"}, "ok": [200]},
    "deepseek": {"url": "https://api.deepseek.com/v1/models",
                 "hdr": lambda k: {"Authorization": f"Bearer {k}"}, "ok": [200]},
    "openai": {"url": "https://api.openai.com/v1/models",
               "hdr": lambda k: {"Authorization": f"Bearer {k}"}, "ok": [200, 429]},
    "github": {"url": "https://api.github.com/user",
               "hdr": lambda k: {"Authorization": f"token {k}"}, "ok": [200, 403]},
    "huggingface": {"url": "https://huggingface.co/api/whoami-v2",
                    "hdr": lambda k: {"Authorization": f"Bearer {k}"}, "ok": [200]},
    "cloudflare": {"url": "https://api.cloudflare.com/client/v4/user/tokens/verify",
                   "hdr": lambda k: {"Authorization": f"Bearer {k}"}, "ok": [200]},
    "telegram": {"url": "https://api.telegram.org/bot{key}/getMe",
                 "hdr": lambda k: {}, "ok": [200]},
}

def buscar_en_directorio(base, servicio, max_archivos=20000):
    """Recorre base buscando tokens del servicio."""
    encontrados = []
    patrones = PATRONES.get(servicio, [])
    if not patrones: return encontrados

    archivos_vistos = 0
    for p in base.rglob("*"):
        if not p.is_file(): continue
        if p.stat().st_size > 5_000_000: continue
        if "/.git/" in str(p) or "node_modules" in str(p): continue
        archivos_vistos += 1
        if archivos_vistos > max_archivos: break
        try: texto = p.read_text(errors="ignore")[:50000]
        except: continue
        for pat in patrones:
            for m in re.finditer(pat, texto):
                tok = m.group(0)
                encontrados.append({"token": tok, "archivo": str(p)})
    return encontrados

def verificar(servicio, token):
    """Prueba el token contra el endpoint del servicio."""
    cfg = VERIFICAR.get(servicio)
    if not cfg: return None
    cmd = ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
           "--max-time", "8", cfg["url"]]
    for h, v in cfg["hdr"](token).items():
        cmd.extend(["-H", f"{h}: {v}"])
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        code = int(r.stdout.strip() or 0)
        return code in cfg["ok"], code
    except: return False, 0

def main():
    if len(sys.argv) < 2:
        print("Uso: python3 buscador_tokens.py <servicio>")
        print(f"Servicios: {', '.join(PATRONES.keys())}")
        return
    servicio = sys.argv[1].lower()

    print(f"═══ BUSCANDO TOKENS DE {servicio.upper()} ═══\n")
    print(f"Buscando en HOME + SD...")

    candidatos = buscar_en_directorio(HOME, servicio, max_archivos=10000)
    candidatos += buscar_en_directorio(SD, servicio, max_archivos=10000)

    # Deduplicar por valor
    vistos = set()
    unicos = []
    for c in candidatos:
        if c["token"] in vistos: continue
        vistos.add(c["token"])
        unicos.append(c)

    print(f"Encontrados: {len(unicos)} candidatos únicos\n")

    if not unicos:
        print("❌ Ninguno. No hay tokens de este servicio en el sistema.")
        print(f"   → Necesita recuperación por email o creación manual")
        return

    # Verificar cada uno
    vivos = []
    for i, c in enumerate(unicos[:20], 1):  # máx 20 para no tardar
        print(f"  [{i}/{min(len(unicos), 20)}] {c['token'][:25]}... ", end="", flush=True)
        ok, code = verificar(servicio, c["token"])
        if ok:
            print(f"✅ HTTP {code}")
            vivos.append(c)
        else:
            print(f"❌ HTTP {code}")

    print(f"\n═══ RESULTADO ═══")
    print(f"Vivos: {len(vivos)}/{len(unicos)}")

    if vivos:
        print(f"\n✅ Tokens vivos encontrados (se pueden AÑADIR al pool):")
        for v in vivos:
            print(f"   {v['token'][:30]}...  en {v['archivo']}")
        # Guardar candidatos verificados para que el usuario decida si sumar
        out = HOME/"miu/state/nuevos_tokens_candidatos.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({
            "servicio": servicio,
            "vivos": [{"token": v["token"], "archivo": v["archivo"]} for v in vivos],
        }, indent=2))
        print(f"\nGuardado en: {out}")
        print("   (para añadir al pool: revisar y aprobar, no automático)")
    else:
        print("❌ Ningún token vivo encontrado.")
        print(f"   → Necesita recuperación por email")

if __name__ == "__main__":
    main()
