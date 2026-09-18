# Jev Mycelio v11.4 - Nodos de fuerza bruta - ρ(x)>0
# Deciders: decisión atómica ms | Explorers: MCTS paralelo | Judge: noul evet/hayır

from dataclasses import dataclass
import random, time

@dataclass
class JevState:
    enemigo_cerca: bool
    phi: float
    carga: float
    lat: int

class JevDecider:
    """No genera texto, solo acción estructurada"""
    def __init__(self, name, fn):
        self.name=name; self.fn=fn
    def act(self, s: JevState):
        t0=time.time()
        action, conf = self.fn(s)
        dt=(time.time()-t0)*1000
        return {"nodo":self.name, "action":action, "conf":conf, "lat_ms":dt, "phi":s.phi}

class JevJudge:
    """noul evet/hayır - poda ramas inútiles"""
    def __init__(self, threshold=0.6):
        self.th=threshold
    def judge(self, result):
        return "evet" if result["conf"]>=self.th else "hayır"

class JevExplorer:
    """MCTS paralelo simple - explora espacio acciones"""
    def explore(self, deciders, state, n=5):
        # paralelo: evalúa n ramas, elige mayor confianza
        results=[d.act(state) for d in deciders for _ in range(n)]
        results.sort(key=lambda x: x["conf"], reverse=True)
        return results[0]

# --- MICELIO DOOM (tu ejemplo) ---
def nodo1_enemigo(s): return ("SI" if s.enemigo_cerca else "NO", 0.99)
def nodo2_atacar_esquivar(s): return ("ATACAR" if s.phi>5 else "ESQUIVAR", 0.9 if s.phi>5 else 0.7)
def nodo3_arma(s): return ("BFG" if s.phi>8 else "SHOTGUN", 0.8 if s.phi>8 else 0.6)

# --- MICELIO MIU (tu router) ---
def decider_ruta_cf(s):
    phi_ruta = s.phi * 1.0 * (1/(1+s.lat/1000)) * (1-s.carga) # 12.4*...
    return (f"cf_01->{phi_ruta:.2f}", phi_ruta/12.4)
def decider_ruta_groq(s):
    phi_ruta = 8.7 * 1.0 * (1/(1+120/1000)) * (1-0.2)
    return (f"groq_01->{phi_ruta:.2f}", phi_ruta/8.7)
def decider_storage_catbox(s):
    return ("catbox https://files.catbox.moe/e59lq4.js", 0.95) # vivo
def decider_storage_0x0(s):
    return ("0x0.st", 0.05) # muerto por botnet spam

# Grafo
judge=JevJudge(0.6)
explorer=JevExplorer()
deciders=[JevDecider("cf",decider_ruta_cf), JevDecider("groq",decider_ruta_groq), JevDecider("catbox",decider_storage_catbox)]

s=JevState(enemigo_cerca=True, phi=10.67, carga=0.1, lat=45)
best=explorer.explore(deciders, s)
print(f"ρ(x)>0 Jev best: {best} -> judge: {judge.judge(best)}")
# Si falla navegación, combate compensa -> sin cerebro central
