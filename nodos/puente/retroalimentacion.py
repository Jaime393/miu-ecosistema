#!/data/data/com.termux/files/usr/bin/python3
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]
MAN = json.load(open(ROOT / "MANIFIESTO_VIVO.json"))
CORPUS = Path(MAN["corpus_unificado_v13"])
PUENTE = ROOT / "nodos/puente/puente_micelio.jsonl"

lines = CORPUS.read_text().splitlines()
# 1. Redundancias: cuántas líneas duplicadas exactas
c = Counter(lines)
redundantes = sum(v-1 for v in c.values() if v>1)
total = len(lines)
unicas = len(c)
print(f"Total {total} | Únicas {unicas} | Redundantes {redundantes} | Ratio {redundantes/total:.2%}")

# 2. Carencias: qué nodos no aportaron
nodos = {}
for nodo_dir in (ROOT / "nodos").iterdir():
    mf = nodo_dir / "MANIFIESTO_NODO.json"
    if mf.exists():
        nodos[nodo_dir.name] = json.load(open(mf))

# 3. Feedback — cubre carencias con redundancias
feedback = {
    "ts": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
    "tipo": "retroalimentacion",
    "suelo": str(MAN["GRACE_TN14"]),
    "stats": {"total": total, "unicas": unicas, "redundantes": redundantes},
    "carencias": [],
    "optimizacion": ""
}
if redundantes/total > 0.3:
    feedback["optimizacion"] = "alta redundancia -> compactar corpus_unificado_v13 dedup + mantener 1 copia en cada nodo como respaldo"
    feedback["carencias"].append("corpus con duplicados de sesiones viejas en Download")
if (ROOT / "data/memoria/micelio_memoria.jsonl").stat().st_size < 200:
    feedback["carencias"].append("micelio_memoria 91 bytes casi vacía -> FranBot debe volcar su oráculo-data.js aquí")
    feedback["optimizacion"] += " | FranBot cubre carencia de memoria"

# Escribe al puente — todos los nodos lo leen
with open(PUENTE, "a") as p:
    p.write(json.dumps(feedback)+"\n")
print(json.dumps(feedback, indent=2))
