#!/usr/bin/env python3
"""nucleo_local — consolida TODO el estado local en un solo archivo.
Sin APIs, sin Supabase, sin Claude. Solo Termux leyendo Termux."""
import hashlib, json, os, re, subprocess, time
from datetime import datetime, timezone
from pathlib import Path

HOME = Path("/data/data/com.termux/files/home")
OUT = HOME / "miu/state/estado_local.json"
LOG = HOME / "miu/state/nucleo_local.log"
OUT.parent.mkdir(parents=True, exist_ok=True)

def ts(): return datetime.now(timezone.utc).isoformat(timespec="seconds")
def sha(s): return hashlib.sha256(s.encode()).hexdigest()[:16]
def log(m):
    with LOG.open("a") as f: f.write(f"[{ts()}] {m}\n")

# Fuentes locales: archivos donde viven tokens, cuentas, claves
FUENTES = [
    HOME/".netrc", HOME/".git-credentials", HOME/".cloudflare.env",
    HOME/".env.cf_auto", HOME/".cloudflare_tokens.json",
    HOME/".miu-panteon-env", HOME/".miu/.env",
    HOME/"miu-ecosistema/.env", HOME/"miu-ecosistema/mesh.env",
    HOME/"miu-ecosistema/canonico.conf", HOME/".bash_history",
    HOME/"miu/state/MIU_TOKEN", HOME/"miu/state/MIU_MESH_URL",
]

# Patrones de token por servicio
PATRONES = {
    "github": r"gh[po]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{80,}",
    "huggingface": r"hf_[A-Za-z0-9]{30,}",
    "cloudflare": r"[A-Za-z0-9_-]{40}",
    "telegram": r"\d{9,12}:[A-Za-z0-9_-]{35,}",
    "openai": r"sk-[A-Za-z0-9]{40,}",
    "groq": r"gsk_[A-Za-z0-9]{40,}",
    "supabase": r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}",
}

def scan_tokens():
    """Busca tokens por servicio en fuentes locales. Deduplica por hash."""
    tokens = {}
    for f in FUENTES:
        if not f.exists(): continue
        try: texto = f.read_text(errors="ignore")[:100000]
        except: continue
        for servicio, patron in PATRONES.items():
            for m in re.finditer(patron, texto):
                tok = m.group(0)
                if "://" in tok or "@" in tok or len(tok) < 20: continue
                h = sha(tok)
                if h in tokens: continue
                tokens[h] = {"servicio": servicio, "longitud": len(tok), "origen": f.name}
    return tokens

def scan_handoffs():
    """Lee handoffs/semillas/mapas recientes (últimos 7 días)."""
    from time import time as now
    corte = now() - 7*86400
    items = []
    for base in [HOME, HOME/"miu/state", HOME/"miu-ecosistema", Path("/storage/25A9-180D")]:
        if not base.exists(): continue
        try:
            for p in base.rglob("*"):
                if not p.is_file(): continue
                n = p.name.lower()
                if not any(k in n for k in ["handoff", "semilla", "seed", "mapa_", "estado_"]): continue
                try: mt = p.stat().st_mtime
                except: continue
                if mt < corte: continue
                items.append({"path": str(p), "nombre": p.name, "edad_h": round((now()-mt)/3600)})
        except: pass
    items.sort(key=lambda x: x["edad_h"])
    return items[:30]

def scan_procesos():
    """Procesos base vivos (los que ya conocemos)."""
    nombres = ["miu_resiliente", "oraculo", "oraculo_borde", "pulse_v153",
               "cloudflared", "tunel_auto", "termux_borde", "cazador_recursos"]
    out = {}
    for n in nombres:
        try:
            r = subprocess.run(["pgrep", "-f", n], capture_output=True, text=True, timeout=3)
            pids = [int(x) for x in r.stdout.split() if x.isdigit()]
            out[n] = {"count": len(pids), "pids": pids}
        except: out[n] = {"count": 0, "pids": []}
    return out

def scan_cuentas_supabase_local():
    """Cuentas_base si está cacheada localmente."""
    for f in [HOME/"miu/state/cuentas_base.json",
              HOME/"miu-ecosistema/.state/cuentas_base.json"]:
        if f.exists():
            try: return json.loads(f.read_text())
            except: pass
    return []

def consolidar():
    """Une todo en un solo archivo."""
    tokens = scan_tokens()
    por_servicio = {}
    for h, t in tokens.items():
        por_servicio.setdefault(t["servicio"], []).append(h)

    estado = {
        "schema": "estado-local-v1",
        "generado": ts(),
        "tokens": {
            "total": len(tokens),
            "por_servicio": {s: len(hs) for s, hs in por_servicio.items()},
            "detalle": tokens,
        },
        "handoffs_recientes": scan_handoffs(),
        "procesos": scan_procesos(),
        "cuentas_base_local": len(scan_cuentas_supabase_local()),
    }

    OUT.write_text(json.dumps(estado, indent=2, ensure_ascii=False))

    # Resumen textual para el log
    log(f"consolidado: {len(tokens)} tokens, "
        f"{len(estado['handoffs_recientes'])} handoffs, "
        f"{sum(1 for p in estado['procesos'].values() if p['count'] > 0)} proc vivos")
    return estado

if __name__ == "__main__":
    e = consolidar()
    print(f"═══ NÚCLEO LOCAL — {e['generado']} ═══")
    print(f"Tokens detectados: {e['tokens']['total']}")
    for s, n in sorted(e['tokens']['por_servicio'].items()):
        print(f"  {s:15} {n}")
    print(f"\nHandoffs recientes: {len(e['handoffs_recientes'])}")
    for h in e['handoffs_recientes'][:5]:
        print(f"  {h['edad_h']:>4}h  {h['nombre'][:60]}")
    print(f"\nProcesos vivos:")
    for n, p in e['procesos'].items():
        icon = "✅" if p['count'] == 1 else ("⚠️ " if p['count'] > 1 else "❌")
        print(f"  {icon} {n:20} × {p['count']}")
    print(f"\nGuardado: {OUT}")
