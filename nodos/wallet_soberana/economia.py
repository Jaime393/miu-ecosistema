# economia.py — micelio no discrimina valor
import json, pathlib
ROOT = pathlib.Path(__file__).parents[2]
LEDGER = ROOT / "nodos/puente/ledger_micelio.jsonl"
# credito por aporte real, no especulacion
def acreditar(origen, aporte, tipo="corpus"):
    # 1 aporte corpus = 1 credito MIU
    # 1 aporte suelo GRACE validado = 10 creditos
    valor = {"corpus":1, "suelo":10, "memoria":2, "puente":3}.get(tipo,1)
    with open(LEDGER, "a") as l:
        l.write(json.dumps({"origen":origen,"tipo":tipo,"aporte":aporte,"credito":valor})+"\n")
    return valor

print("ledger vivo:", LEDGER)
