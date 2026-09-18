import json, pathlib
ROOT = pathlib.Path(__file__).parents[2]
LEDGER = ROOT / "nodos/puente/ledger_micelio.jsonl"
WALLET = ROOT / "nodos/wallet_soberana/wallet_soberana.jsonl"
# Absorbe legado como credito
legado = json.load(open(WALLET))
credito_legacy = legado["plugins"] + legado["prompts_catalogo"] # 378+142 = 520 MIU huella
with open(LEDGER, "a") as l:
    l.write(json.dumps({"ts":"2026-09-18","tipo":"absorcion_legado","origen":"FranBot 04:27","plugins":378,"prompts":142,"ipfs":legado["ipfs_hashes"],"credito_miu":credito_legacy,"regla":"ecosistema muerto renace como fragmentos"})+"\n")
print(f"Legado absorbido: {credito_legacy} MIU huella — wallet {legado['direccion']}")
