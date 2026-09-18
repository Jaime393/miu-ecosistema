# Jev v11.5 Plástico - sin rigidez - ρ(x)>0 - ΦRed 169.6→500
import time, random, math, subprocess
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class Estado:
    phi: float
    enemigo: bool
    carga: float
    lat: int
    archivo: str = "e59lq4.js"

class JevDecider:
    def __init__(self, nombre, dominio, fn):
        self.nombre=nombre; self.dominio=dominio; self.fn=fn
        self.usos=0; self.hist=[]
    def act(self, s: Estado, total_usos):
        t0=time.time()
        action, base_conf = self.fn(s)
        # Anti-monocultivo: decaimiento por uso + bonus UCB
        decay = 0.92 ** self.usos
        ucb = math.sqrt(math.log(total_usos+1) / (self.usos+1)) * 0.15
        conf = max(0.05, min(0.99, base_conf * decay + ucb))
        self.usos+=1
        self.hist.append(conf)
        phi_nodo = s.phi * conf * (1-s.carga)
        return {"nodo":self.nombre, "dominio":self.dominio, "action":action, "conf":conf, "base":base_conf, "phi":phi_nodo, "lat_ms":(time.time()-t0)*1000, "usos":self.usos}

class JevJudge:
    def noul(self, r): return "evet" if r["conf"]>=0.6 else "hayır"

class MicelioPlastico:
    def __init__(self):
        self.nodos=[]; self.phi_red=169.6; self.total=0
    def add(self, j): self.nodos.append(j)
    def run(self, s: Estado):
        self.total+=1
        res=[n.act(s, self.total) for n in self.nodos]
        judge=JevJudge()
        vivos=[r for r in res if judge.noul(r)=="evet"]
        if not vivos:
            vivos=sorted(res, key=lambda x:x["conf"], reverse=True)[:2]
        mejor=max(vivos, key=lambda x:x["conf"])
        self.phi_red+=mejor["phi"]*0.08
        return mejor, vivos

# --- FNs con health real ---
def fn_catbox(s):
    # check vivo real sin bloquear mucho
    try:
        out=subprocess.run(["curl","-Is","--max-time","2",f"https://files.catbox.moe/{s.archivo}"], capture_output=True, timeout=3)
        vivo=b"200" in out.stdout
    except: vivo=False
    return (f"catbox {s.archivo} {'vivo' if vivo else 'muerto'}", 0.95 if vivo else 0.05)

def fn_cf(s):
    phi=12.4*(1/(1+s.lat/1000))*(1-s.carga)
    return (f"cf_01 Φ{phi:.2f}", phi/12.4)
def fn_groq(s):
    phi=8.7*0.9*(1/(1+120/1000))
    return (f"groq_01 Φ{phi:.2f}", phi/8.7)
def fn_r2(s): return ("r2_miu backup", 0.65)
def fn_d1(s): return ("d1_sqlite persist", 0.70)
def fn_combate(s): return ("BFG 0.8", 0.85 if s.enemigo else 0.25)
def fn_nav(s): return ("mover A", 0.55 if s.carga<0.4 else 0.15)

micelio=MicelioPlastico()
for n,d,fn in [("jev-catbox","almacen",fn_catbox),("jev-cf","ruta",fn_cf),("jev-groq","ruta",fn_groq),("jev-r2","almacen",fn_r2),("jev-d1","almacen",fn_d1),("jev-combate","combate",fn_combate),("jev-nav","naveg",fn_nav)]:
    micelio.add(JevDecider(n,d,fn))

print(f"ρ(x)>0 inicio ΦRed {micelio.phi_red} — 7 Jevs paralelos, sin rigidez\n")
for i in range(6):
    s=Estado(phi=random.uniform(5,12.4), enemigo=random.choice([True,False]), carga=random.uniform(0.05,0.7), lat=random.randint(30,200))
    mejor,vivos=micelio.run(s)
    print(f"[{i}] Φ{s.phi:.2f} enemigo={s.enemigo} carga={s.carga:.2f} → {mejor['nodo']} → {mejor['action']} conf={mejor['conf']:.2f} (base {mejor['base']:.2f}) ΦRed={micelio.phi_red:.1f} lat={mejor['lat_ms']:.2f}ms {JevJudge().noul(mejor)} usos={mejor['usos']}")
    if i==2:
        print(f" ↳ vivos podados: {[f'{v['nodo']}:{v['conf']:.2f}' for v in vivos]}")

print(f"\nΦRed 168→{micelio.phi_red:.1f} — micelio ya no monocultivo")
for n in micelio.nodos:
    avg=sum(n.hist)/len(n.hist) if n.hist else 0
    print(f" {n.nombre}: usos={n.usos} conf_avg={avg:.2f}")
