#!/usr/bin/env python3
"""descubrir_familias — agrupa tokens por formato (no por servicio conocido).
Detecta familias nuevas. Reporta al usuario para que las clasifique."""
import hashlib, json, re, subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HOME = Path("/data/data/com.termux/files/home")
STATE = HOME / "miu/state"
OUT = STATE / "familias_descubiertas.json"
STATE.mkdir(parents=True, exist_ok=True)

# Fuentes donde buscar tokens
FUENTES = [
    HOME/"tokens_raw.txt", HOME/".netrc", HOME/".git-credentials",
    HOME/".bash_history", HOME/".cloudflare.env", HOME/".env.cf_auto",
    HOME/".cloudflare_tokens.json", HOME/".miu-panteon-env",
    HOME/"miu-ecosistema/.env", HOME/"miu-ecosistema/mesh.env",
    HOME/"miu-ecosistema/canonico.conf", HOME/".miu/.env",
    Path("/storage/25A9-180D/biblioteca_miu/config/claves.env"),
    Path("/storage/25A9-180D/biblioteca_miu/todo/miu-ecosistema/.vault.json"),
    Path("/storage/25A9-180D/biblioteca_miu/todo/miu-ecosistema/nutrientes/recursos_cazados.json"),
    Path("/storage/25A9-180D/.miu-base/earthdata_token.json"),
]

# Prefijos conocidos → servicio (para clasificar automáticamente)
PREFIJOS_CONOCIDOS = {
    "sk-ant-":       ("anthropic", "Anthropic (sk-ant-api03-...)"),
    "sk-proj-":      ("openai",    "OpenAI project key"),
    "sk-or-":        ("openrouter","OpenRouter"),
    "gsk_":          ("groq",      "Groq"),
    "hf_":           ("huggingface","HuggingFace"),
    "ghp_":          ("github",    "GitHub personal token"),
    "gho_":          ("github",    "GitHub OAuth"),
    "ghs_":          ("github",    "GitHub server"),
    "github_pat_":   ("github",    "GitHub fine-grained"),
    "gldt-":         ("gitlab",    "GitLab"),
    "xoxb-":         ("slack",     "Slack bot"),
    "xoxp-":         ("slack",     "Slack user"),
    "shpat_":        ("shopify",   "Shopify"),
    "pypi-":         ("pypi",      "PyPI"),
    "AKIA":          ("aws",       "AWS access key"),
    "AIza":          ("google",    "Google API key"),
    "ya29.":         ("google",    "Google OAuth"),
    "SG.":           ("sendgrid",  "SendGrid"),
    "cfat_":         ("cloudflare","Cloudflare API token (nuevo)"),
    "cfut_":         ("cloudflare","Cloudflare user token"),
    "eyJ":           ("jwt",       "JWT (Supabase/Earthdata/Google)"),
    "sk-":           ("openai",    "OpenAI/DeepSeek clásico"),
}

def clasificar_por_prefijo(tok):
    """Busca el prefijo más largo que matchea."""
    for prefijo in sorted(PREFIJOS_CONOCIDOS.keys(), key=len, reverse=True):
        if tok.startswith(prefijo):
            return PREFIJOS_CONOCIDOS[prefijo]
    return None, None

def inferir_por_formato(tok):
    """Si no matchea prefijo, inferir por longitud+charset."""
    n = len(tok)
    if all(c in "0123456789abcdef" for c in tok.lower()):
        if n == 32: return ("hex32", "MD5-like o DeepSeek o clave hex 32")
        if n == 40: return ("hex40", "SHA1-like o token hex 40")
        if n == 64: return ("hex64", "SHA256-like o Together/Cohere")
        if n == 96: return ("hex96", "hex 96 chars")
    if all(c in "0123456789abcdefABCDEF" for c in tok):
        return (f"hex{n}", f"hex {n} chars")
    if tok.isdigit():
        return (f"num{n}", f"numérico {n} dígitos (IDs, Make/Zapier)")
    if re.match(r'^[A-Za-z0-9+/]{20,}={0,2}$', tok):
        return (f"b64{n}", f"base64-like {n} chars")
    return (f"opaco{n}", f"opaco {n} chars")

def agrupar():
    """Agrupa todos los tokens por familia (prefijo o formato)."""
    familias = defaultdict(lambda: {"tokens": [], "servicios_sugeridos": set(),
                                    "descripcion": "", "origenes": set()})

    for fuente in FUENTES:
        if not fuente.exists(): continue
        try: texto = fuente.read_text(errors="ignore")[:200000]
        except: continue
        # Todos los strings 20+ chars
        for m in re.finditer(r'[A-Za-z0-9_\-\.:/+]{20,}', texto):
            tok = m.group(0)
            if "://" in tok or "@" in tok: continue
            if len(tok) < 20 or len(tok) > 500: continue

            servicio, desc = clasificar_por_prefijo(tok)
            if servicio:
                clave = f"prefijo:{tok[:12].split('_')[0].split('-')[0]}"
                familias[clave]["servicios_sugeridos"].add(servicio)
                familias[clave]["descripcion"] = desc
            else:
                familia, desc_fmt = inferir_por_formato(tok)
                clave = f"formato:{familia}"
                familias[clave]["descripcion"] = desc_fmt

            h = hashlib.sha256(tok.encode()).hexdigest()[:12]
            if h not in [t["sha"] for t in familias[clave]["tokens"]]:
                familias[clave]["tokens"].append({
                    "sha": h, "preview": tok[:25] + "...", "len": len(tok),
                })
            familias[clave]["origenes"].add(fuente.name)

    # Convertir sets a listas (JSON serializable)
    resultado = {}
    for clave, data in familias.items():
        resultado[clave] = {
            "descripcion": data["descripcion"],
            "servicios_sugeridos": sorted(data["servicios_sugeridos"]),
            "cantidad": len(data["tokens"]),
            "muestra": data["tokens"][:5],
            "origenes": sorted(data["origenes"]),
        }

    # Ordenar por cantidad
    return dict(sorted(resultado.items(), key=lambda x: -x[1]["cantidad"]))

def main():
    print(f"═══ DESCUBRIMIENTO DE FAMILIAS — {datetime.now(timezone.utc).isoformat(timespec='seconds')} ═══\n")
    print("Escaneando todas las fuentes...\n")

    familias = agrupar()
    total = sum(f["cantidad"] for f in familias.values())

    print(f"Familias detectadas: {len(familias)}")
    print(f"Tokens únicos totales: {total}\n")

    # Separar conocidas vs nuevas
    conocidas = [(k, v) for k, v in familias.items() if v["servicios_sugeridos"]]
    desconocidas = [(k, v) for k, v in familias.items() if not v["servicios_sugeridos"]]

    print(f"═══ FAMILIAS CONOCIDAS ({len(conocidas)}) ═══")
    for k, v in conocidas:
        serv = ",".join(v["servicios_sugeridos"])
        print(f"  {k:25} {v['cantidad']:3} tokens → {serv}")
        print(f"       {v['descripcion']}")

    if desconocidas:
        print(f"\n═══ FAMILIAS DESCONOCIDAS ({len(desconocidas)}) ═══")
        print("  (el sistema no sabe qué servicio son, pero los detecta)")
        for k, v in desconocidas:
            print(f"  {k:25} {v['cantidad']:3} tokens")
            print(f"       {v['descripcion']}")
            if v["muestra"]:
                print(f"       muestra: {v['muestra'][0]['preview']}")
            print(f"       origenes: {', '.join(v['origenes'][:3])}")

    # Guardar
    payload = {
        "schema": "familias-tokens-v1",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total_familias": len(familias),
        "total_tokens": total,
        "conocidas": len(conocidas),
        "desconocidas": len(desconocidas),
        "familias": familias,
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    print(f"\n📄 Guardado: {OUT}")
    print(f"\n   Próximo paso: revisar las desconocidas")
    print(f"   Si reconoces alguna (Cohere/Together/Make/etc), dímela")
    print(f"   y añado el endpoint de verificación")

if __name__ == "__main__":
    main()
