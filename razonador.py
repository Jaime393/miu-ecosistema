#!/usr/bin/env python3
"""razonador — piensa con los tokens reales del sistema.
Fallback: deepseek → groq → anthropic → openai."""
import json, re, subprocess, sys
from pathlib import Path

HOME = Path("/data/data/com.termux/files/home")
FUENTES = [
    HOME / "tokens_raw.txt",
    Path("/storage/25A9-180D/biblioteca_miu/config/claves.env"),
    Path("/storage/25A9-180D/biblioteca_miu/todo/miu-ecosistema/.vault.json"),
]
PATRONES = {
    "deepseek":  r"sk-[a-f0-9]{32}",
    "anthropic": r"sk-ant-[A-Za-z0-9_\-]{40,}",
    "groq":      r"gsk_[A-Za-z0-9]{40,}",
    "openrouter": r"sk-or-v1-[A-Za-z0-9]{40,}",
    "openai":    r"sk-[A-Za-z0-9]{40,}",
}
ENDPOINTS = {
    "deepseek":  "https://api.deepseek.com/v1/chat/completions",
    "anthropic": "https://api.anthropic.com/v1/messages",
    "groq":      "https://api.groq.com/openai/v1/chat/completions",
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
    "openai":    "https://api.openai.com/v1/chat/completions",
}
MODELOS = {
    "groq":      "openai/gpt-oss-120b",
    "deepseek":  "deepseek-chat",
    "anthropic": "claude-3-5-haiku-20241022",
    "openrouter": "meta-llama/llama-3.3-70b-instruct",
    "openai":    "gpt-4o-mini",
}

# Fallback de modelos por si uno está ocupado/deprecado
FALLBACK_MODELOS = {
    "groq": ["openai/gpt-oss-120b", "qwen/qwen3.8-27b", "openai/gpt-oss-20b", "allam-2-7b"],
}

def extraer_tokens():
    tokens = {s: [] for s in PATRONES}
    for f in FUENTES:
        if not f.exists(): continue
        try: t = f.read_text(errors="ignore")[:500000]
        except: continue
        for s, pat in PATRONES.items():
            for m in re.finditer(pat, t):
                if m.group(0) not in tokens[s]:
                    tokens[s].append(m.group(0))
    return tokens

def llamar(servicio, token, prompt, max_tokens=300):
    modelos = FALLBACK_MODELOS.get(servicio, [MODELOS[servicio]])
    for modelo in modelos:
        resp, err = _llamar_uno(servicio, token, modelo, prompt, max_tokens)
        if resp is not None:
            return resp, None
    return None, err if modelos else "sin modelo"

def _llamar_uno(servicio, token, modelo, prompt, max_tokens):
    body = {"model": modelo, "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}]}
    if servicio == "anthropic":
        h = ["-H", f"x-api-key: {token}", "-H", "anthropic-version: 2023-06-01",
             "-H", "content-type: application/json"]
    else:
        h = ["-H", f"Authorization: Bearer {token}", "-H", "content-type: application/json"]
    try:
        r = subprocess.run(["curl","-s","--max-time","30","-X","POST",
                            ENDPOINTS[servicio]] + h + ["-d", json.dumps(body)],
                           capture_output=True, text=True, timeout=35)
        if r.returncode != 0: return None, f"curl {r.returncode}"
        d = json.loads(r.stdout)
    except Exception as e:
        return None, str(e)[:80]
    if servicio == "anthropic":
        c = d.get("content", [])
        if c and c[0].get("type") == "text": return c[0]["text"], None
        return None, d.get("error", {}).get("message", "sin respuesta")
    choices = d.get("choices", [])
    if choices: return choices[0].get("message", {}).get("content", ""), None
    return None, d.get("error", {}).get("message", "sin respuesta")

def razonar(prompt, max_tokens=300):
    tokens = extraer_tokens()
    errores = []
    for s in ["groq", "openrouter", "deepseek", "anthropic", "openai"]:
        for t in tokens.get(s, []):
            resp, err = llamar(s, t, prompt, max_tokens)
            if resp:
                return {"ok": True, "servicio": s, "respuesta": resp, "intentos": len(errores)}
            errores.append(f"{s}:{err[:40]}")
    return {"ok": False, "error": "ningún servicio", "intentos": errores}

if __name__ == "__main__":
    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Responde en una frase: ¿qué es la coherencia?"
    print(json.dumps(razonar(prompt), indent=2, ensure_ascii=False))
