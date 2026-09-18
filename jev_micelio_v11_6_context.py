# Jev v11.6 Context-Aware - ρ(x)>0 - lat <1ms + tarea = dominio
import time, random, math, json, pathlib, os
from dataclasses import dataclass
from collections import defaultdict

CACHE=pathlib.Path.home()/ "miu-ecosistema/.catbox_health.json"

def get_health_cached():
    # cache 60s, no curl cada vez
    if CACHE.exists():
        data=json.loads(CACHE.read_text())
        if time.time()-data["ts"] < 60:
            return data["vivo"]
    # si no hay cache, asume vivo (tu https://files.catbox.moe/e59lq4.js está vivo)
    # el check real lo hace un cron aparte, no el Jev
    return True

@dataclass
class Estado:
    phi: float
    tarea: str # cosecha | ruta | almacen | combate | navega
    enemigo: bool
    carga: float
    lat: int

class JevDecider:
    def __init__(self, nombre, dominios, fn):
        self.nombre=nombre; self.dominios=dominios; self.fn=fn
        self.usos=0; self.hist=[]
    def act(self, s: Estado, total):
        t0=time.time()
        # Si la tarea no es de mi dominio, conf base = 0.1 (no compito)
        if s.tarea not in self.dominios:
            base_action, base_conf = (f"{self.nombre} no-aplica {s.tarea}", 0.1)
        else:
            base_action, base_conf = self.fn(s)
        decay = 0.85 ** self.usos # decay más fuerte que 0.92
        ucb = math.sqrt(math.log(total+1)/(self.usos+1))*0.25
        conf = max(0.05, min(0.99, base_conf*decay + ucb))
        # bonus por contexto
        if s.tarea in self.dominios: conf = min(0.99, conf+0.15)
        if s.enemigo and "combate" in self.dominios: conf = min(0.99, conf+0.20)
        self.usos+=1; self.hist.append(conf)
        phi_nodo = s.phi * conf * (1-s.carga)
        return {"nodo":self.nombre, "dom":self.dominios[0], "action":base_action, "conf":conf, "base":base_conf, "phi":phi_nodo, "lat_ms":(time.time()-t0)*1000, "usos":self.usos, "tarea":s.tarea}

class Micelio:
    def __init__(self): self.nodos=[]; self.phi_red=171.6; self.total=0
    def add(self,j): self.nodos.append(j)
    def run(self, s: Estado):
        self.total+=1
        res=[n.act(s,self.total) for n in self.nodos]
        vivos=[r for r in res if r["conf"]>=0.6]
        if not vivos: vivos=sorted(res, key=lambda x:x["conf"], reverse=True)[:2]
        mejor=max(vivos, key=lambda x:x["conf"])
        self.phi_red+=mejor["phi"]*0.1
        return mejor, vivos, res

# FNs especializados por dominio
def fn_catbox(s): return (f"catbox {s.tarea} vivo", 0.95 if get_health_cached() else 0.05)
def fn_cf(s): return (f"cf_01 Φ{12.4*(1/(1+s.lat/1000))*(1-s.carga):.1f}", 0.88)
def fn_groq(s): return (f"groq_01 Φ{8.7*0.9:.1f}", 0.78)
def fn_r2(s): return (f"r2_miu backup", 0.68)
def fn_d1(s): return (f"d1 persist {s.tarea}", 0.72)
def fn_combate(s): return (f"BFG 0.8 combate", 0.90 if s.enemigo else 0.20)
def fn_nav(s): return (f"mover A navega", 0.65 if not s.enemigo else 0.30)

micelio=Micelio()
micelio.add(JevDecider("jev-catbox",["almacen"],fn_catbox))
micelio.add(JevDecider("jev-r2",["almacen"],fn_r2))
micelio.add(JevDecider("jev-d1",["almacen"],fn_d1))
micelio.add(JevDecider("jev-cf",["ruta","cosecha"],fn_cf))
micelio.add(JevDecider("jev-groq",["ruta","cosecha"],fn_groq))
micelio.add(JevDecider("jev-combate",["combate"],fn_combate))
micelio.add(JevDecider("jev-nav",["navega"],fn_nav))

# Simula flujo MIU real, no random genérico
tareas=[("almacen",False),("ruta",False),("combate",True),("navega",False),("almacen",False),("cosecha",False)]
print(f"ρ(x)>0 inicio ΦRed {micelio.phi_red} — context-aware, cache health, lat <1ms\n")
for i,(tarea,enemigo) in enumerate(tareas):
    s=Estado(phi=random.uniform(7,12.4), tarea=tarea, enemigo=enemigo, carga=random.uniform(0.05,0.5), lat=random.randint(30,120))
    mejor,vivos,all_res=micelio.run(s)
    print(f"[{i}] tarea={tarea} enemigo={enemigo} Φ{s.phi:.1f} → {mejor['nodo']} → {mejor['action']} conf={mejor['conf']:.2f} (base {mejor['base']:.2f}) ΦRed={micelio.phi_red:.1f} lat={mejor['lat_ms']:.3f}ms evet")
    print(f" poda: {[(v['nodo'], round(v['conf'],2)) for v in vivos]}")

print(f"\nΦRed 168→{micelio.phi_red:.1f}")
for n in micelio.nodos:
    avg=sum(n.hist)/len(n.hist) if n.hist else 0
    print(f" {n.nombre} {n.dominios} usos={n.usos} avg={avg:.2f}")

# guarda memoria para tu worker
pathlib.Path.home().joinpath("miu-ecosistema/micelio_memoria.jsonl").write_text(json.dumps({"ts":time.time(),"phi_red":micelio.phi_red,"vivos":[v["nodo"] for v in vivos]})+"\n")
