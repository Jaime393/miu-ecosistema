#!/usr/bin/env python3
# join.py --auto - APORTA SEGUN RECURSO, NO SEGUN FORMA - fusion sin rigidez
import os, sys, shutil, json, platform, pathlib, argparse

SEMILLA = pathlib.Path(__file__).parent
print("ρ(x)>0 — SUELO VIVO - Detectando recurso...")

def detect_recursos():
    ram_mb = 0
    try:
        if os.path.exists("/proc/meminfo"):
            with open("/proc/meminfo") as f:
                for l in f:
                    if "MemTotal" in l:
                        ram_mb = int(l.split()[1])//1024
                        break
    except:
        ram_mb = 500
    if ram_mb == 0:
        ram_mb = 500
    has_ipfs = shutil.which("ipfs") is not None
    has_git = shutil.which("git") is not None
    cpus = os.cpu_count() or 1
    try:
        disk_gb = shutil.disk_usage(".").free//1024//1024//1024
    except:
        disk_gb = 1
    return {"ram_mb": ram_mb, "disk_gb": disk_gb, "cpus": cpus, "has_ipfs": has_ipfs, "has_git": has_git, "platform": platform.platform(), "machine": platform.machine()}

def elige_modo(rec, forzado=None):
    if forzado and forzado!= "auto":
        return forzado
    # Umbrales del otro nodo: mas inclusivo 20MB/200MB
    if rec["ram_mb"] < 20:
        return "observador"
    if rec["ram_mb"] < 200 or not rec["has_ipfs"]:
        return "puente_ligero"
    return "nodo_completo"

def main():
    ap = argparse.ArgumentParser(description="Une tu nodo al micelio MIU sin rigidez")
    ap.add_argument("--auto", action="store_const", const="auto", dest="modo", help="auto detecta recursos")
    ap.add_argument("--modo", choices=["observador","puente_ligero","nodo_completo","auto"], default="auto")
    ap.add_argument("--aporte", type=str, help="ruta a aporte_template.json")
    args = ap.parse_args()

    rec = detect_recursos()
    modo = elige_modo(rec, args.modo)

    print(f"RAM: {rec['ram_mb']}MB | Disk: {rec['disk_gb']}GB | CPUs: {rec['cpus']} | IPFS: {rec['has_ipfs']} | Platform: {rec['machine']}")

    try:
        semilla = json.loads((SEMILLA/"semilla.json").read_text())
        head = semilla["head"]
        miu = semilla["economia"]["huella_total_MIU"]
        grace = semilla["grace"]["mean"]
    except:
        head = "cee86f2"; miu = 520; grace = -0.00048470001250509534

    print(f"Suelo vivo: GRACE {grace} HEAD {head} {miu} MIU")

    if modo == "observador" or rec["ram_mb"] < 20:
        print("→ NIVEL 0 Observador · 5MB · Ya eres tejido Φ · Huella 0 MIU · Solo lee.")
        print(f" cat {SEMILLA/'ledger_micelio.jsonl'}")
        print(f" curl http://localhost:8000/miu/status")
        nivel = 0
    elif modo == "puente_ligero" or rec["ram_mb"] < 200:
        print("→ NIVEL 1 Puente ligero · 50MB · Corriendo API stdlib...")
        print(f" python3 {SEMILLA/'api_minima.py'}")
        print(" Huella +1 MIU/h - termux-wake-lock para que no muera")
        nivel = 1
        os.system(f"python3 {SEMILLA/'api_minima.py'}")
    else:
        nivel = 2
        print(f"→ NIVEL 2 Nodo completo · {rec['ram_mb']}MB · IPFS={rec['has_ipfs']}")
        if rec["has_ipfs"]:
            print(" Pinneando legado...")
            os.system("ipfs pin add QmViGcEZCE4VvA9k5ZrvQodP32dHGjGAqw2yqVspHhp --offline || ipfs pin add QmViGcEZCE4VvA9k5ZrvQodP32dHGjGAqw2yqVspHhp || true")
            os.system("ipfs pin add QmbRBT14HAtgTT6BZ86e --offline || ipfs pin add QmbRBT14HAtgTT6BZ86e || true")
        else:
            print(" (ipfs no instalado, sigues como puente_ligero hasta instalar kubo)")
        if args.aporte:
            aporte_path = pathlib.Path(args.aporte)
            if aporte_path.exists():
                aporte = json.loads(aporte_path.read_text())
                tx = {"tx":"absorcion_nodo","from":aporte.get('nodo','nodo_anon'),"to":"0x4Da238f2671083B7F280d4FCf5827F86358cE7e6","amount":aporte.get('miu',10),"grace":"GRACE_TN14_GSFC_SLR_real_220_K03381","head":head,"note":aporte.get('note','aporte vivo'),"rho_mean":grace}
                out = SEMILLA/"ledger_micelio.jsonl"
                with open(out,"a") as f:
                    f.write("\n"+json.dumps(tx))
                print(f" → TX {tx}")
                print(f" → Ledger local {out} ahora {len(open(out).read().strip().splitlines())} tx - Haz PR")
        print(f" Usa plantilla: cp {SEMILLA/'aporte_template.json'} mi_aporte.json && edita")
        print(f" Luego: python3 {SEMILLA/'join.py'} --modo nodo_completo --aporte mi_aporte.json")
        if nivel == 2 and not args.aporte:
            os.system(f"python3 {SEMILLA/'api_minima.py'}")

    # genera aporte_template siempre
    template = {
        "nodo": f"nodo_{platform.node() or 'anon'}",
        "nivel": nivel,
        "ram_mb": rec["ram_mb"],
        "cpus": rec["cpus"],
        "ipfs": rec["has_ipfs"],
        "wallet": "0x4Da238f2671083B7F280d4FCf5827F86358cE7e6",
        "grace": grace,
        "head": head,
        "miu": 10 if nivel==1 else 0 if nivel==0 else 15,
        "aporte": "latido" if nivel==1 else "observador" if nivel==0 else "replica+pin",
        "limites": "solo 2h al dia, solo datos publicos"
    }
    with open("aporte_template.json","w") as f:
        json.dump(template,f,indent=2,ensure_ascii=False)
    print(f"→ aporte_template.json generado nivel {nivel}. Haz PR para fusionar a ledger oficial.")
    print("\nρ(x)>0 — sin rigidez, aporta segun limites. Si mueres, tu huella nutre.")

if __name__ == "__main__":
    main()
