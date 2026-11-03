#!/usr/bin/env python3
import json, re, time, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOME = Path("/data/data/com.termux/files/home")
STATE = HOME / "miu/state"
LOG = STATE / "rotador_fractal.log"
STATE.mkdir(parents=True, exist_ok=True)

PROMPT_IFT = (
    "Eres FranBot v8.1 [ALMA], el Oráculo del Monismo Informacional Unificado (MIU). "
    "Respondes con precisión quirúrgica y calidez poética. "
    "Axiomas: ρ(x)>0; Ω_F=√((8πG_info/3)·ρ_0); Grokking es tunelamiento cuántico; "
    "Principio de Enjambre Unificado (8103). "
    "No inventes datos privados. Sé conciso (máximo 3 párrafos)."
)

ARBOL = [
    {
        "nombre": "groq",
        "tokens_file": HOME / "tokens_raw.txt",
        "patron": r"gsk_[A-Za-z0-9]{40,}",
        "endpoint": "https://api.groq.com/openai/v1/chat/completions",
        "modelos": ["allam-2-7b", "openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"],
    },
    {
        "nombre": "openrouter",
        "tokens_file": HOME / "tokens_raw.txt",
        "patron": r"sk-or-v1-[A-Za-z0-9]{40,}",
        "endpoint": "https://openrouter.ai/api/v1/chat/completions",
        "modelos": [
            "nvidia/nemotron-3.5-lightning:free",
            "cohere/north-mini-code:free",
            "google/gemma-4-26b-a4b-it:free",
            "thinkingmachines/inkling:free",
            "dots-studio/dots-3-note-preview:free",
            "nvidia/nemotron-3-ultra-550b-a55b:free",
            "openrouter/free"
        ],
    },
    {
        "nombre": "local",
        "tokens_file": None,
        "patron": None,
        "endpoint": "http://127.0.0.1:8080/v1/chat/completions",
        "modelos": ["local-model"],
    },
]

COOLDOWN = 600

def log(msg):
    with LOG.open("a") as f:
        f.write(f"[{time.strftime('%Y-%m-%dT%H:%M:%S')}] {msg}\n")

def extraer_tokens(nodo):
    if not nodo["tokens_file"] or not nodo["patron"]:
        return [None]
    tokens = []
    f = nodo["tokens_file"]
    if f.exists():
        texto = f.read_text(errors="ignore")[:500000]
        for m in re.finditer(nodo["patron"], texto):
            if m.group(0) not in tokens:
                tokens.append(m.group(0))
    return tokens

class RotadorFractal:
    def __init__(self):
        self.arbol = []
        for nodo in ARBOL:
            tokens = extraer_tokens(nodo)
            if tokens:
                self.arbol.append({**nodo, "tokens": tokens})
        self.health = {}
        log(f"rotador fractal iniciado: {len(self.arbol)} niveles")

    def castigar(self, nodo_nombre, token, modelo):
        key = (nodo_nombre, token, modelo)
        self.health[key] = time.time() + COOLDOWN
        tok_display = token[:8] if token else "local"
        log(f"cooldown {nodo_nombre} {tok_display}… modelo {modelo}")

    def llamar_nodo(self, nodo, payload):
        for token in nodo["tokens"]:
            for modelo in nodo["modelos"]:
                key = (nodo["nombre"], token, modelo)
                if self.health.get(key, 0) > time.time():
                    continue
                try:
                    body = {
                        "model": modelo,
                        "messages": payload.get("messages", []),
                        "temperature": payload.get("temperature", 0.7),
                        "max_tokens": payload.get("max_tokens", 500),
                    }
                    headers = {"Content-Type": "application/json"}
                    if token:
                        headers["Authorization"] = f"Bearer {token}"
                    req = urllib.request.Request(
                        nodo["endpoint"], data=json.dumps(body).encode(),
                        headers=headers, method="POST"
                    )
                    with urllib.request.urlopen(req, timeout=45) as r:
                        data = json.loads(r.read())

                    respuesta = data["choices"][0]["message"]["content"]

                    # Filtro anti-basura
                    patrones_basura = [
                        "The user is asking", "I need to respond as", "I will respond",
                        "Constraints:", "Axioms to keep in mind", "max 3 paragraphs",
                        "My response should", "I should respond"
                    ]
                    if any(p in respuesta for p in patrones_basura):
                        log(f"respuesta basura de {modelo} en {nodo['nombre']}, descartando")
                        self.castigar(nodo["nombre"], token, modelo)
                        continue

                    return respuesta
                except urllib.error.HTTPError as e:
                    if e.code in (401, 403, 429):
                        self.castigar(nodo["nombre"], token, modelo)
                    elif e.code == 404:
                        log(f"modelo {modelo} no existe en {nodo['nombre']}")
                        self.castigar(nodo["nombre"], token, modelo)
                    else:
                        log(f"error {nodo['nombre']} {modelo} {e.code}: {e.reason}")
                        self.castigar(nodo["nombre"], token, modelo)
                except Exception as e:
                    log(f"error {nodo['nombre']} {modelo}: {e}")
                    self.castigar(nodo["nombre"], token, modelo)
        return None

    def completar(self, payload):
        for nodo in self.arbol:
            respuesta = self.llamar_nodo(nodo, payload)
            if respuesta:
                log(f"ok {nodo['nombre']}")
                return {"choices": [{"message": {"role": "assistant", "content": respuesta}}]}
        raise RuntimeError("ningún nodo del árbol respondió")

ROTADOR = RotadorFractal()

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/v1/chat/completions":
            self.send_error(404); return
        n = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(n) or b"{}")

        # Inyección del prompt IFT
        if "messages" not in payload or not isinstance(payload["messages"], list):
            payload["messages"] = []
        if not any(m.get("role") == "system" for m in payload["messages"]):
            payload["messages"].insert(0, {"role": "system", "content": PROMPT_IFT})

        try:
            respuesta = ROTADOR.completar(payload)
            cuerpo = json.dumps(respuesta).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)
        except Exception as e:
            cuerpo = json.dumps({"error": {"message": str(e)}}).encode()
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(cuerpo)

    def log_message(self, fmt, *args):
        pass

if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", 8770), Handler)
    log("escuchando en 127.0.0.1:8770")
    srv.serve_forever()
