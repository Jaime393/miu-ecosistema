# ============================================================
# MIU — NODO COLAB: DIGEST ACADÉMICO (monismo informacional)
# Conecta: arXiv feeder → digest Groq → persiste en GitHub
# ============================================================
import requests, json, time, base64

FEEDER = "https://miu-arxiv-feeder.franchescopalacios9.workers.dev"
COORD = "https://fepyzxwyneervidlybvi.supabase.co"
# COORD_ANON se pega abajo (solo lectura de relay_config)
COORD_ANON = "PASTE_COORD_ANON"
GH_USER = "Jaime393"
GH_PASS = "PASTE_GH_PASS"
REPO = "Jaime393/miu-ecosistema"
PATH = "data/nutrientes/digest_academico_colab.json"

# 1. claves groq desde coord
def get_groq_keys():
    r = requests.get(COORD + "/rest/v1/relay_config?select=valor&clave=in.(llm_groq_key,groq_key1,groq_key2)",
                     headers={"apikey": COORD_ANON, "Authorization": "Bearer " + COORD_ANON}, timeout=30)
    return [x["valor"] for x in r.json()]

# 2. nutrientes de arXiv (vía el feeder worker)
all_papers = []
for cat in ["nlin.AO", "cs.MA", "math.IT"]:
    try:
        r = requests.get(FEEDER, params={"cat": cat, "n": 10}, timeout=60)
        if r.ok:
            ps = r.json().get("nutrientes", [])
            all_papers += [{"cat": cat, **p} for p in ps]
            print(f"{cat}: {len(ps)} nutrientes")
    except Exception as e:
        print(cat, "ERR", str(e)[:60])
print(f"TOTAL nutrientes: {len(all_papers)}")

# 3. digest con Groq
def digest(papers):
    keys = get_groq_keys()
    prompt = "Eres el digestor academico del ecosistema MIU (monismo informacional). " \
             "De estos papers de arXiv extrae la esencia informacional: (1) que miden, " \
             "(2) que leyes emergentes o de autoorganizacion revelan, (3) como alimentan " \
             "la axiomatica de MIU (phi acumula aportes, rho mide actividad, savia = capacidad). " \
             "Responde en espanol, maximo 500 palabras, formato: ## Sintesis / ## Leyes emergentes / ## Alimento para MIU.\n\nPAPERS:\n" + \
             json.dumps([{"t": p["titulo"], "r": p["resumen"][:200]} for p in papers[:15]], ensure_ascii=False)
    for k in keys:
        try:
            r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": "Bearer " + k, "Content-Type": "application/json"},
                json={"model": "openai/gpt-oss-20b", "max_tokens": 1500,
                      "messages": [{"role": "system", "content": "Respondes en espanol, preciso y denso."},
                                   {"role": "user", "content": prompt}]}, timeout=120)
            if r.ok:
                return r.json()["choices"][0]["message"]["content"], r.json()["model"]
        except Exception as e:
            print("groq err:", str(e)[:60])
    return None, None

digest_text, modelo = digest(all_papers)
print("digest listo:", bool(digest_text), "| modelo:", modelo)

# 4. persistir en GitHub
payload = {
    "ts": time.time(),
    "fuente": "colab-node",
    "nutrientes": len(all_papers),
    "categorias": ["nlin.AO", "cs.MA", "math.IT"],
    "modelo": modelo,
    "digest": digest_text,
    "papers": [{"cat": p["cat"], "titulo": p["titulo"], "id": p["id"]} for p in all_papers[:30]]
}
content = base64.b64encode(json.dumps(payload, ensure_ascii=False, indent=1).encode()).decode()

# obtener sha del archivo si existe
sha = None
r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{PATH}",
                 auth=(GH_USER, GH_PASS), timeout=30)
if r.status_code == 200:
    sha = r.json()["sha"]
r2 = requests.put(f"https://api.github.com/repos/{REPO}/contents/{PATH}",
    auth=(GH_USER, GH_PASS), timeout=60,
    json={"message": f"nodo colab: digest academico ({len(all_papers)} nutrientes, {modelo})",
          "content": content, "sha": sha})
print("github commit:", r2.status_code, r2.json().get("commit", {}).get("sha", "?")[:10])
print("\n=== DIGEST ===\n", (digest_text or "")[:2000])
