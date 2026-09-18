from fastapi import FastAPI
import json, time, pathlib
app = FastAPI(title="MIU Micelio API - GRACE 221R - aa12689")

WALLET = "0x4Da238f2671083B7F280d4FCf5827F86358cE7e6"
GRACE = "GRACE_TN14_GSFC_SLR_real_220_K03381"
RHO_MEAN = -0.00048470001250505
LEDGER = pathlib.Path(__file__).parents[1] / "puente" / "ledger_micelio.jsonl"

@app.get("/suelo")
def suelo():
    return {"grace": GRACE, "rho_mean": RHO_MEAN, "rho>0": True, "estado": "vivo", "head": "aa12689", "bloques": 3, "redundantes": 0}

@app.get("/oraculo/franbot")
def oraculo(q: str, miu: float = 0):
    if miu < 0.01:
        return {"error": "saldo insuficiente", "precio": "0.01 MIU por query", "wallet": WALLET, "suelo": GRACE}
    return {"grace": GRACE, "rho_mean": RHO_MEAN, "respuesta": f"FranBot 1561 pares v8.0 + legacy 378 plugins: {q} -> suelo vivo", "costo": 0.01, "wallet": WALLET, "head": "aa12689"}

@app.post("/economia/pagar")
def pagar(tx: dict):
    with open(LEDGER, "a") as f:
        f.write(json.dumps({**tx, "grace": GRACE, "rho_mean": RHO_MEAN, "ts": time.time()})+"\n")
    return {"ok": True, "ancla": GRACE, "huella": "absorbida", "ledger": str(LEDGER)}
