#!/usr/bin/env python3
"""Prueba cfut_ y hex64. Si vivos, los suma al pool."""
import json, re, subprocess
from datetime import datetime, timezone
from pathlib import Path

HOME = Path("/data/data/com.termux/files/home")
OUT = HOME / "miu/state/nuevos_tokens_verificados.json"
OUT.parent.mkdir(parents=True, exist_ok=True)

def cargar_tokens():
    """Extrae cfut_ y hex64 de todos los archivos."""
    fuentes = [HOME/"tokens_raw.txt", HOME/".netrc", HOME/".bash_history",
               HOME/".cloudflare.env", HOME/".cloudflare_tokens.json",
               Path("/storage/25A9-180D/biblioteca_miu/config/claves.env"),
               Path("/storage/25A9-180D/biblioteca_miu/todo/miu-ecosistema/.vault.json"),
               Path("/storage/25A9-180D/biblioteca_miu/todo/miu-ecosistema/nutrientes/recursos_cazados.json")]
    cfuts, hex64s = set(), set()
    for f in fuentes:
        if not f.exists(): continue
        try: texto = f.read_text(errors="ignore")[:200000]
        except: continue
        for m in re.finditer(r'cfut_[A-Za-z0-9_\-]{30,}', texto):
            cfuts.add(m.group(0))
        for m in re.finditer(r'ncfut_[A-Za-z0-9_\-]{30,}', texto):
            cfuts.add(m.group(0)[1:])  # quitar la 'n'
        # hex64: exactamente 64 hex chars, no parte de algo más largo
        for m in re.finditer(r'(?<![a-zA-Z0-9])[a-f0-9]{64}(?![a-zA-Z0-9])', texto):
            hex64s.add(m.group(0))
    return sorted(cfuts), sorted(hex64s)

def curl_status(url, headers, timeout=10):
    cmd = ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
           "--max-time", str(timeout)]
    for k, v in headers.items():
        cmd.extend(["-H", f"{k}: {v}"])
    cmd.append(url)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+5)
        return int(r.stdout.strip() or 0)
    except: return 0

def probar_cfut(tok):
    """CF user token → verify endpoint."""
    code = curl_status(
        "https://api.cloudflare.com/client/v4/user/tokens/verify",
        {"Authorization": f"Bearer {tok}"}
    )
    return code == 200, code

def probar_hex64(tok):
    """Probar contra Cohere, Together, HuggingFace."""
    resultados = {}
    # Cohere
    code = curl_status("https://api.cohere.ai/v1/models",
        {"Authorization": f"Bearer {tok}", "accept": "application/json"})
    resultados["cohere"] = code
    # Together
    code = curl_status("https://api.together.xyz/v1/models",
        {"Authorization": f"Bearer {tok}"})
    resultados["together"] = code
    # HF (por si es un token HF sin prefijo hf_)
    code = curl_status("https://huggingface.co/api/whoami-v2",
        {"Authorization": f"Bearer {tok}"})
    resultados["huggingface"] = code
    return resultados

def main():
    print(f"═══ CLASIFICAR NUEVOS ═══\n")
    cfuts, hex64s = cargar_tokens()
    print(f"cfut_ encontrados: {len(cfuts)}")
    print(f"hex64 encontrados: {len(hex64s)}\n")

    resultado = {
        "schema": "nuevos-tokens-verificados-v1",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "cloudflare": [],
        "hex64": [],
    }

    # ── CF ──
    print("── Cloudflare (cfut_) ──")
    cf_vivos = 0
    for tok in cfuts:
        vivo, code = probar_cfut(tok)
        icon = "✅" if vivo else "❌"
        print(f"  {icon} {tok[:30]}...  HTTP {code}")
        if vivo: cf_vivos += 1
        resultado["cloudflare"].append({"token": tok, "sha": __import__("hashlib").sha256(tok.encode()).hexdigest()[:12],
                                         "http": code, "vivo": vivo})
    print(f"\n  Vivos: {cf_vivos}/{len(cfuts)}\n")

    # ── hex64 ──
    print("── hex64 (Cohere/Together/HF) ──")
    for tok in hex64s:
        res = probar_hex64(tok)
        ganadores = [k for k, c in res.items() if c == 200]
        icon = "✅" if ganadores else "❌"
        print(f"  {icon} {tok[:30]}...  {res}")
        resultado["hex64"].append({
            "token": tok, "sha": __import__("hashlib").sha256(tok.encode()).hexdigest()[:12],
            "servicios_ok": ganadores, "http": res,
        })

    OUT.write_text(json.dumps(resultado, indent=2, ensure_ascii=False))
    print(f"\n📄 {OUT}")

if __name__ == "__main__":
    main()
