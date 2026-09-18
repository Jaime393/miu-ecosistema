#!/usr/bin/env python3
import os, json, pathlib, platform, shutil, sys, argparse

SEMILLA=pathlib.Path(__file__).parent
print("ρ(x)>0 — JOIN micelio sin rigidez")

def detect_recursos():
    ram_mb=0
    try:
        import psutil
        ram_mb=psutil.virtual_memory().total//1024//1024
    except:
        try:
            with open("/proc/meminfo") as f:
                for l in f:
                    if l.startswith("MemTotal"):
                        ram_mb=int(l.split()[1])//1024
                        break
        except: ram_mb=512
    disk_gb=shutil.disk_usage(".").free//1024//1024//1024
    cpus=os.cpu_count() or 1
    has_ipfs=shutil.which("ipfs") is not None
    has_git=shutil.which("git") is not None
    return {"ram_mb":ram_mb,"disk_gb":disk_gb,"cpus":cpus,"has_ipfs":has_ipfs,"has_git":has_git,"platform":platform.platform()}

def elige_modo(rec, forzado=None):
    if forzado: return forzado
    if rec["ram_mb"]<100: return "observador"
    if rec["ram_mb"]<400 or not rec["has_ipfs"]: return "puente_ligero"
    return "nodo_completo"

def main():
    ap=argparse.ArgumentParser(description="Une tu nodo al micelio MIU sin rigidez")
    ap.add_argument("--auto", action="store_const", const="auto", dest="modo", help="auto detecta recursos" )
    ap.add_argument("--modo", choices=["observador","puente_ligero","nodo_completo","auto"], default="auto")
    ap.add_argument("--aporte", type=str, help="ruta a aporte_template.json con tus plugins/prompts")
    args=ap.parse_args()
    rec=detect_recursos()
    print(f"Recursos detectados: {rec}")
    modo=elige_modo(rec, None if args.modo=="auto" else args.modo)
    print(f"→ Modo elegido: {modo} (forzado={args.modo})")
    semilla=json.loads((SEMILLA/"semilla.json").read_text())
    print(f"Suelo vivo: GRACE {semilla['grace']['mean']} HEAD {semilla['head']} {semilla['economia']['huella_total_MIU']} MIU")
    if modo=="observador":
        print("Nivel 0 — Observador: no necesitas correr nada. Lee ledger_micelio.jsonl")
        print(f" cat {SEMILLA/'ledger_micelio.jsonl'}")
        print(" Huella 0 MIU, ya eres tejido Φ")
    elif modo=="puente_ligero":
        print("Nivel 1 — Puente ligero: corre API minima stdlib")
        print(f" python3 {SEMILLA/'api_minima.py'}")
        print(" Deja corriendo en Termux con termux-wake-lock")
        print(" Huella +1 MIU/h")
    else:
        print("Nivel 2 — Nodo completo: replica + aporta")
        print(f" python3 {SEMILLA/'api_minima.py'} &")
        if rec["has_ipfs"]:
            print(" ipfs pin add QmViGcEZCE4VvA9k5ZrvQodP32dHGjGAqw2yqVspHhp --offline || true")
        else:
            print(" (ipfs no instalado, sigues como puente_ligero hasta instalar kubo)")
        if args.aporte:
            aporte=json.loads(pathlib.Path(args.aporte).read_text())
            print(f" Aporte detectado: {aporte}")
            tx={"tx":"absorcion_nodo","from":aporte.get('nodo','nodo_anon'),"to":semilla['economia']['wallet_soberana'],"amount":aporte.get('miu',10),"grace":semilla['grace']['dataset'],"head":semilla['head'],"note":aporte.get('note','aporte vivo'),"rho_mean":semilla['grace']['mean']}
            print(f" TX propuesta: {tx}")
            out=SEMILLA/"ledger_micelio.jsonl"
            with open(out,"a") as f: f.write("\n"+json.dumps(tx))
            print(f" → Ledger local actualizado {out} ahora {len(open(out).read().strip().splitlines())} tx")
            print(" → Haz PR a Jaime393/miu-ecosistema con tu tx")
        else:
            print(f" Usa plantilla: cp {SEMILLA/'aporte_template.json'} mi_aporte.json && edita")
            print(f" Luego: python3 {SEMILLA/'join.py'} --modo nodo_completo --aporte mi_aporte.json")
    print("\nρ(x)>0 — sin rigidez, aporta segun limites. Si mueres, tu huella nutre.")

if __name__=="__main__": main()
