# Jev Micelio v11.4 Expandido - sin rigidez - ρ(x)>0
import random, time, asyncio
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class Estado:
    phi: float
    enemigo_cerca: bool
    carga: float
    lat: int
    archivo: str = "e59lq4.js"

class JevDecider:
    def __init__(self, nombre, dominio, fn):
        self.nombre=nombre; self.dominio=dominio; self.fn=fn; self.conf_historica=[]
    def act(self, s: Estado):
        t0=time.time()
        action, conf = self.fn(s)
        dt=(time.time()-t0)*1000
        self.conf_historica.append(conf)
        # Φ individual crece si conf alta
        phi_nodo = s.phi * conf * (1 - s.carga)
        return {"nodo":self.nombre, "dominio":self.dominio, "action":action, "conf":conf, "phi":phi_nodo, "lat_ms":dt}

class JevJudge:
    def __init__(self, th=0.6):
        self.th=th
    def noul(self, res):
        # evet/hayır calibrado
        return "evet" if res["conf"] >= self.th else "hayır"

class Micelio:
    def __init__(self):
        self.nodos=[]
        self.conexiones=defaultdict(list)
        self.phi_red=168
    def add_jev(self, jev):
        self.nodos.append(jev)
    def conectar(self, de, a):
        self.conexiones[de].append(a)
    def crecer(self, resultados):
        # Crece hacia nodos con más confianza
        mejor = max(resultados, key=lambda x: x["conf"])
        self.phi_red += mejor["phi"] * 0.1
        return mejor
    def run(self, estado):
        # Deciders paralelos - todos actúan sin esperar
        resultados = [n.act(estado) for n in self.nodos]
        # Judge poda
        judge=JevJudge()
        vivos = [r for r in resultados if judge.noul(r)=="evet"]
        if not vivos:
            return {"action":"FALLBACK_combate_reacciona", "conf":0.7, "phi_red":self.phi_red}
        # Explorer elige mejor rama (MCTS simple)
        mejor = self.crecer(vivos)
        # Si navegación falla, combate compensa
        if mejor["dominio"]=="navegacion" and mejor["conf"]<0.5:
            combates=[r for r in vivos if r["dominio"]=="combate"]
            if combates: mejor=max(combates, key=lambda x:x["conf"])
        return mejor

# --- JEvs especializados MIU ---
def jev_cosecha(s): return ("cosecha router 10.67", 0.92 if s.phi>5 else 0.4)
def jev_enrutar_cf(s):
    phi_ruta = 12.4 * 1.0 * (1/(1+s.lat/1000)) * (1-s.carga)
    return (f"cf_01 Φ{phi_ruta:.2f}", phi_ruta/12.4)
def jev_enrutar_groq(s):
    phi_ruta = 8.7 * 1.0 * (1/(1+120/1000)) * 0.8
    return (f"groq_01 Φ{phi_ruta:.2f}", phi_ruta/8.7)
def jev_store_catbox(s): return (f"catbox https://files.catbox.moe/{s.archivo} vivo", 0.95)
def jev_store_0x0(s): return ("0x0.st muerto botnet", 0.05)
def jev_verifica(s): return ("verifica ΦRed", 0.88)
def jev_combate(s): return ("BFG 0.8 | Shotgun 0.2", 0.8 if s.enemigo_cerca else 0.3)
def jev_navegacion(s): return ("mover A", 0.6 if s.carga<0.5 else 0.2)

# Construcción micelio
micelio=Micelio()
for nombre,dominio,fn in [
    ("jev-cosecha","cosecha",jev_cosecha),
    ("jev-cf","enrutamiento",jev_enrutar_cf),
    ("jev-groq","enrutamiento",jev_enrutar_groq),
    ("jev-catbox","almacenamiento",jev_store_catbox),
    ("jev-0x0","almacenamiento",jev_store_0x0),
    ("jev-verifica","verificacion",jev_verifica),
    ("jev-combate","combate",jev_combate),
    ("jev-nav","navegacion",jev_navegacion),
]:
    micelio.add_jev(JevDecider(nombre,dominio,fn))

micelio.conectar("jev-cosecha","jev-cf")
micelio.conectar("jev-cf","jev-catbox")
micelio.conectar("jev-nav","jev-combate") # si nav falla -> combate

# Doom + MIU en un loop
for i in range(3):
    estado=Estado(phi=10.67 if i==0 else random.uniform(3,12), enemigo_cerca=random.choice([True,False]), carga=random.uniform(0.05,0.6), lat=random.randint(30,180))
    decision=micelio.run(estado)
    print(f"[{i}] Estado Φ{estado.phi:.2f} enemigo={estado.enemigo_cerca} → {decision['nodo']} → {decision['action']} conf={decision['conf']:.2f} ΦRed={micelio.phi_red:.1f} lat={decision['lat_ms']:.3f}ms evet")

print(f"\nΦRed 168→{micelio.phi_red:.1f} — micelio creció hacia {max(micelio.nodos, key=lambda n: sum(n.conf_historica)/len(n.conf_historica) if n.conf_historica else 0).nombre}")
