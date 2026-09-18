#!/data/data/com.termux/files/usr/bin/python3
# puente.py — interconecta nodos autónomos, sin rutas hardcodeadas
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
MAN_VIVO = ROOT / "MANIFIESTO_VIVO.json"
PUENTE = ROOT / "nodos/puente/puente_micelio.jsonl"

man = json.load(open(MAN_VIVO))
# cada nodo aporta
for nodo_dir in (ROOT / "nodos").iterdir():
    if not nodo_dir.is_dir(): continue
    mf = nodo_dir / "MANIFIESTO_NODO.json"
    if mf.exists():
        print(f"nodo {nodo_dir.name} vivo: {json.load(open(mf))['tipo']}")

# flujo: FranBot -> corpus -> artemis quality -> suelo GRACE -> memoria
with open(PUENTE, "a") as p:
    p.write(json.dumps({"ts": __import__("datetime").datetime.utcnow().isoformat(), "evento": "puente vivo", "suelo": man["GRACE_TN14"]})+"\n")
print(f"puente escrito {PUENTE}")
