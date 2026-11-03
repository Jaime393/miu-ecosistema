#!/usr/bin/env python3
"""inventario_dispositivo — extrae tokens de archivos del sistema y verifica cuáles viven."""
import hashlib, json, re, subprocess
from datetime import datetime, timezone
from pathlib import Path

HOME = Path("/data/data/com.termux/files/home")
SD = Path("/storage/25A9-180D")
OUT = HOME / "miu/state/inventario_dispositivo.json"

ARCHIVOS = [
    SD/"FranBot/secrets.json",
    SD/"FranBot/tokens.env",
    SD/"FranBot/_credenciales/raw/claves.env",
    SD/"FranBot/_credenciales/raw/secrets.json",
    SD/"FranBot/_credenciales/raw/claves_ssh.json",
    SD/"FranBot/claves_ssh.json",
    SD/"FranBot_clon/config/secrets.json",
    SD/"FranBot_backup/config/secrets.json",
    SD/"config/secrets.json",
    SD/"config/telegram_token.txt",
    SD/"cognitive/all_credentials.json",
    SD/"Music/proyecto_alma_completo.json",
    SD/"FranBot/_backup_proxy_20260728_170951/apis.json.bak",
    SD/"FranBot/lightpanda",
]

PATRONES = {
    "cloudflare": r"cf(?:ut|at)_[A-Za-z0-9_\-]{30,}",
    "groq":       r"gsk_[A-Za-z0-9]{40,}",
    "deepseek":   r"sk-[a-f0-9]{32}",
    "anthropic":  r"sk-ant-[A-Za-z0-9_\-]{40,}",
    "openai":     r"sk-(?:proj|svcacct)-[A-Za-z0-9_\-]{40,}",
    "huggingface":r"hf_[A-Za-z0-9]{30,}",
    "github":     r"gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{80,}",
    "telegram":   r"\d{9,12}:[A-Za-z0-9_-]{35,}",
    "openrouter": r"sk-or-v1-[A-Za-z0-9]{64,}",
    "cohere":     r"[a-zA-Z0-9]{40}",
    "vercel":     r"vcp_[A-Za-z0-9]{40,}",
    "supabase_jwt": r"eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}",
}

def extraer():
    """Extrae tokens únicos por servicio de todos los archivos."""
    tokens = {}
    for f in ARCHIVOS:
        if not f.exists() or not f.is_file(): continue
        try:
            if f.stat().st_size > 5_000_000: continue
            texto = f.read_text(errors="ignore")
        except: continue
        for servicio, pat in PATRONES.items():
            for m in re.finditer(pat, texto):
                tok = m.group(0)
                h = hashlib.sha256(tok.encode()).hexdigest()[:12]
                if h in tokens: continue
                tokens[h] = {"servicio": servicio, "token": tok, "origen": str(f)}
    return tokens

ENDPOINTS = {
    "cloudflare": {"url": "https://api.cloudflare.com/client/v4/user/tokens/verify",
                   "hdr": lambda k: {"Authorization": f"Bearer {k}"}, "ok": [200]},
    "groq":       {"url": "https://api.groq.com/openai/v1/models",
                   "hdr": lambda k: {"Authorization": f"Bearer {k}"}, "ok": [200, 429]},
    "deepseek":   {"url": "https://api.deepseek.com/user/balance",
                   "hdr": lambda k: {"Authorization": f"Bearer {k}"}, "ok": [200]},
    "anthropic":  {"url": "https://api.anthropic.com/v1/models",
                   "hdr": lambda k: {"x-api-key": k, "anthropic-version": "2023-06-01"}, "ok": [200]},
    "huggingface":{"url": "https://huggingface.co/api/whoami-v2",
                   "hdr": lambda k: {"Authorization": f"Bearer {k}"}, "ok": [200]},
    "github":     {"url": "https://api.github.com/user",
                   "hdr": lambda k: {"Authorization": f"token {k}"}, "ok": [200, 403]},
    "telegram":   {"url": "https://api.telegram.org/bot{key}/getMe",
                   "hdr": lambda k: {}, "ok": [200]},
    "openrouter": {"url": "https://openrouter.ai/api/v1/auth/key",
                   "hdr": lambda k: {"Authorization": f"Bearer {k}"}, "ok": [200]},
}

def verificar(servicio, token):
    ep = ENDPOINTS.get(servicio)
    if not ep: return None, 0
    url = ep["url"].replace("{key}", token)
    hdr = {k: v.replace("{key}", token) for k, v in ep["hdr"](token).items()}
    cmd = ["curl","-s","-o","/dev/null","-w","%{http_code}","--max-time","10", url]
    for k, v in hdr.items(): cmd.extend(["-H", f"{k}: {v}"])
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        code = int(r.stdout.strip() or 0)
        return code in ep["ok"], code
    except: return False, 0

def main():
    print("═══ INVENTARIO DISPOSITIVO ═══\n")
    tokens = extraer()
    print(f"Tokens únicos extraídos: {len(tokens)}\n")

    # Cargar pool actual para comparar
    pool_file = SD / ".miu-base/cf_tokens_todos.txt"
    pool_cf = set(t.strip() for t in pool_file.read_text().splitlines() if t.strip()) if pool_file.exists() else set()

    resultado = {"schema": "inventario-dispositivo-v1",
                 "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "total_extraidos": len(tokens),
                 "por_servicio": {},
                 "vivos": [],
                 "muertos": [],
                 "nuevos_vs_pool": []}

    por_servicio = {}
    for h, info in tokens.items():
        por_servicio.setdefault(info["servicio"], []).append((h, info))

    for servicio, items in sorted(por_servicio.items()):
        print(f"── {servicio} ({len(items)}) ──")
        for h, info in items:
            tok = info["token"]
            vivo, code = verificar(servicio, tok)
            es_nuevo = servicio == "cloudflare" and tok not in pool_cf
            icon = "✅" if vivo else ("?" if vivo is None else "❌")
            marca = " [NUEVO]" if es_nuevo and vivo else ""
            print(f"  {icon} {h} HTTP {code:3} {info['origen'].split('/')[-1]}{marca}")
            entry = {"servicio": servicio, "sha": h, "token": tok,
                     "origen": info["origen"], "http": code, "vivo": bool(vivo)}
            if vivo: resultado["vivos"].append(entry)
            else: resultado["muertos"].append(entry)
            if es_nuevo and vivo: resultado["nuevos_vs_pool"].append(entry)
        print()

    resultado["por_servicio"] = {s: len(v) for s, v in por_servicio.items()}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(resultado, indent=2, ensure_ascii=False))

    print(f"═══ RESUMEN ═══")
    print(f"  Vivos:         {len(resultado['vivos'])}")
    print(f"  Muertos:       {len(resultado['muertos'])}")
    print(f"  CF nuevos:     {len(resultado['nuevos_vs_pool'])}")
    print(f"\n📄 {OUT}")

if __name__ == "__main__":
    main()
