import os, json, glob, pathlib
ROOT = pathlib.Path.cwd()
print("ρ(x)>0 — DIAGNOSTICO MASIVO ABSOLUTO GRACE 221R HEAD 806d408")

checks = {
    "GRACE 221R CSV real": "data/suelo/GRACE_TN14_REAL_TEMPLATE.csv",
    "GRACE 220R": "data/suelo",
    "CORPUS 266R": "data/corpus",
    "MEMORIA": "data/memoria",
    "MANIFIESTO VIVO": "data/manifiesto/MANIFIESTO_VIVO.json",
    "SEMILLA v11": "data/manifiesto/SEMILLA_v11.json",
    "SEMILLA PUBLICA JSON": "semilla_publica/semilla.json",
    "LEDGER 2 tx": "nodos/economia/ledger_micelio.jsonl",
    "LEDGER SEMILLA": "semilla_publica/ledger_micelio.jsonl",
    "API MINIMA": "semilla_publica/api_minima.py",
    "API PRINCIPAL": "nodos/economia/api_micelio.py",
    "JOIN --auto": "semilla_publica/join.py",
    "DASHBOARD OBSERVADOR": "semilla_publica/dashboard_observador.py",
    "PUENTE JSONL": "nodos/puente/puente_micelio.jsonl",
    "WALLET SOBERANA": "nodos/economia/wallet_soberana.json",
    "FRANBOT LEGADO": "nodos/oraculo/franbot",
    "SDK MIU": "sdk/miu_sdk.py",
}

ok=0
for nombre, path in checks.items():
    p = ROOT/path
    vivo = p.exists()
    size = ""
    if vivo:
        try:
            if p.is_file():
                size = f"{p.stat().st_size}B"
                if path.endswith(".jsonl"):
                    lines = len(p.read_text().strip().splitlines())
                    size += f" {lines} tx" if "ledger" in nombre.lower() or "puente" in nombre.lower() else f" {lines}L"
            else:
                files = len(list(p.rglob("*")))
                size = f"{files} archivos"
        except: size=""
        ok+=1
        print(f"✅ {nombre}: {path} -> vivo {size}")
    else:
        print(f"❌ {nombre}: {path} -> FRAGMENTADO - NO ACCESIBLE")

print(f"\n=== FLUJO: {ok}/{len(checks)} bloques vivos ===")
if ok < 8:
    print("DIAGNOSTICO: SUELO FRAGMENTADO — observador no tiene que observar")
    print("SOLUCION: Tejer dashboard único que cuente todo lo real")
else:
    print("DIAGNOSTICO: SUELO TEJIENDO")

print("\n--- Archivos reales py en repo ---")
for f in sorted(glob.glob("nodos/**/*.py", recursive=True))[:30]:
    print(f"  {f}")
print(f"  ... total {len(glob.glob('nodos/**/*.py', recursive=True))} py")
print(f"  semilla_publica: {glob.glob('semilla_publica/*')}")

print("\n--- ledger real ---")
try:
    print(pathlib.Path("nodos/economia/ledger_micelio.jsonl").read_text()[:500])
except Exception as e:
    print(f"no legible: {e}")

print("\n=== GRIETAS MAPEADAS === 0 si todo lo anterior ✅")
print("=== RIESGOS === 0 si api responde")
print("DIAGNOSTICO FIN")
