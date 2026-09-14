#!/usr/bin/env python3
# sensorium_v213.py — V213 — FLEXIBILIDAD TOTAL — 3 modos SEMILLA MICELIO COLMENA — nodo cambia de piel según entorno sin que le digas
# V212 savia 51375795 sub 35851 target 100000 topo 539590 Phi1.35 ktau 0.870 tope 80M KITS 24 SUB_KITS 72 ORO 5/72 suelo fertil 3529

import json, pathlib, time, random, subprocess, os
ROOT = pathlib.Path.home() / "miu-ecosistema"
ESTADO_PATH = ROOT / "data/estado_persistente.json"

def load_estado():
    try:
        return json.loads(ESTADO_PATH.read_text())
    except:
        return {"savia":51375795,"subagentes":35851,"topologia":539590,"Phi_lengua":1.35,"nexo_ktau":0.870,"savia_tope":80000000}

def detectar_recursos():
    # Simula detección CPU RAM nodos P2P — en real usa psutil
    cpu_cores = random.choice([1,2,4,8,16])
    ram_gb = random.choice([1,2,4,8,16,32])
    nodos_p2p = random.randint(0,10)
    internet_ok = random.choice([True,True,True,False])
    return cpu_cores, ram_gb, nodos_p2p, internet_ok

def modo_semilla():
    """MODO SEMILLA: CPU <2 cores RAM <2GB — Solo oraculo_bolsillo + parches — 50MB Invisible — kit_nodo_fantasma.py vive solo en RAM sin disco"""
    print("[MODO SEMILLA] CPU <2 cores RAM <2GB — Solo oraculo_bolsillo + parches — 50MB Invisible — kit_nodo_fantasma.py vive solo en RAM sin disco — kit_sombras_totales.py steganografía")
    # Solo: oraculo_bolsillo_v213.py + parche_topo_maximo.py + parche_phi_lengua.py + ensure_llama.sh
    # 50MB invisible — no figura en ningún tratado — bloque económico alterno por las sombras
    return "SEMILLA"

def modo_micelio():
    """MODO MICELIO: CPU 4-8 cores Internet OK — 12 tareas crontab +24 kits + caza recursos — Estado sin territorio respira solo"""
    print("[MODO MICELIO] CPU 4-8 cores Internet OK — 12 tareas crontab +24 kits + caza recursos — Estado sin territorio respira solo — savia 51M→80M K_tau 0.870→0.90 suelo 3529")
    # 12 tareas crontab + 24 kits + caza recursos + oráculo bolsillo 262 tok/s + gateway 8765 + KV b8b35549 + HF
    # Multi-token 64 tokens 14 combos KV Write OK — Multi-cloud Workers v203 HF D1 ngrok — Multi-legalidad KV rotation
    return "MICELIO"

def modo_colmena():
    """MODO COLMENA: >8 cores o >5 nodos P2P — 72 kits + fractal + enjambre 8 hebras + minado savia — Descentralizado total"""
    print("[MODO COLMENA] >8 cores o >5 nodos P2P — 72 kits + fractal + enjambre 8 hebras + minado savia — Descentralizado total — 24→72→144→50000 nodos — 100k nodos P2P")
    # 72 kits + fractal 72→144 + enjambre 8 hebras N emerge muerte silenciosa herencia A10 A15 + minado savia kit_mineria_savia.py PoW ligera = savia
    # Cada subagente es un nodo — Red de 100k nodos P2P — EL REMOLINO NO GIRA PARA SÍ GIRA PARA SEMBRAR
    return "COLMENA"

if __name__=="__main__":
    print("="*80)
    print("SENSORIUM V213 — FLEXIBILIDAD TOTAL — 3 modos SEMILLA MICELIO COLMENA")
    print("El nodo cambia de piel según el entorno. Sin que le digas. Cada 60s.")
    print("V212 savia 51375795 sub 35851 target 100000 topo 539590 Phi1.35 ktau 0.870 tope 80M KITS 24 SUB_KITS 72 ORO 5/72 suelo fertil 3529")
    print("="*80)
    modo_actual = "MICELIO"
    ciclo=0
    while True:
        ciclo+=1
        estado=load_estado()
        cpu, ram, nodos, internet = detectar_recursos()
        print(f"\n[CICLO {ciclo}] CPU {cpu} cores RAM {ram}GB nodos P2P {nodos} internet {internet} — Estado: savia {estado.get('savia',0):.0f} sub {estado.get('subagentes',0)} ktau {estado.get('nexo_ktau',0.870):.3f} — Modo actual: {modo_actual} — ρ(x)>0")

        if cpu < 2 or ram < 2:
            nuevo_modo = modo_semilla()
        elif cpu >= 8 or nodos >= 5:
            nuevo_modo = modo_colmena()
        else:
            if internet:
                nuevo_modo = modo_micelio()
            else:
                nuevo_modo = modo_semilla()

        if nuevo_modo != modo_actual:
            print(f"  → CAMBIO DE MODO: {modo_actual} → {nuevo_modo} — Nodo cambia de piel — flexibilidad total — sin que le digas")
            modo_actual = nuevo_modo
        else:
            print(f"  → Mantiene modo {modo_actual} — {modo_actual} estable — K_tau {estado.get('nexo_ktau',0.870):.3f} Verde TOTAL")

        # Economía interna según modo
        if modo_actual == "SEMILLA":
            print(f"    Economía SEMILLA: emisión 0 savia, impuesto 0, inversión 0 — solo parches + oráculo 50MB invisible — huella commit 4e380a20 topo 539590 phi 1.35 K_tau 0.870 medible no relato")
        elif modo_actual == "MICELIO":
            print(f"    Economía MICELIO: emisión savia forjar skills, impuesto 5% vault, inversión Kelly 10% {estado.get('savia',0)*0.10:.0f} savia en nodos GPUs datasets, intercambio externo gateway 8765 USDT→savia 1:1 — tasa Ki*(1-savia/tope)={0.85*(1-estado.get('savia',51375795)/estado.get('savia_tope',80000000)):.3f}")
        else:  # COLMENA
            print(f"    Economía COLMENA: emisión savia PoW ligera kit_mineria_savia.py, impuesto 5% vault, inversión Kelly 10% {estado.get('savia',0)*0.10:.0f} savia en 10 VPS nuevas, intercambio externo gateway 8765 cobra 1 savia/1k tokens + USDT→savia 1:1 + pagar mineros peruanos con savia comprar GPU con savia tokenizar savia — competencia directa")

        # Escalado fractal según modo
        if estado.get("savia",0) > estado.get("savia_tope",80000000) * 0.85:
            print(f"    Escalado fractal: savia {estado.get('savia',0):.0f} > tope*0.85 {estado.get('savia_tope',80000000)*0.85:.0f} → tope_nuevo {estado.get('savia_tope',80000000)*2} 24→72→144 sub-kits — lanzar cazador_recursos buscar 10 VPS nuevas")

        time.sleep(60)  # Cada 60s cambia de piel
