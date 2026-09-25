"""
MIU - Motor de Grafo de Lenguaje con FST
ρ(x)>0 - Redes de Transducción Finita para TTS/ASR
V24 8001 vivo - Cabeza micelial

FST = Finite State Transducer (q, input, output, next_q, weight)
Usado para:
- Normalización texto → fonemas (TTS)
- Fonemas → texto (ASR)
- Lema + K_τ → Φ
"""
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import json, math

@dataclass
class ArcoFST:
    origen: str
    entrada: str   # ε = ""
    salida: str    # ε = ""
    destino: str
    peso: float = 0.0  # -log prob, K_τ compatible

class FST:
    def __init__(self, nombre="micelio_fst"):
        self.nombre=nombre
        self.estados=set()
        self.inicial=None
        self.finales=set()
        self.arcos: List[ArcoFST]=[]
        self._idx: Dict[str, List[ArcoFST]]={}

    def add_estado(self, q, inicial=False, final=False):
        self.estados.add(q)
        if inicial: self.inicial=q
        if final: self.finales.add(q)
        self._idx.setdefault(q, [])

    def add_arco(self, origen, entrada, salida, destino, peso=0.0):
        self.estados.update([origen,destino])
        a=ArcoFST(origen,entrada,salida,destino,peso)
        self.arcos.append(a)
        self._idx.setdefault(origen, []).append(a)

    def transduce(self, entrada: List[str], max_paths=3) -> List[Tuple[List[str], float]]:
        """entrada lista de simbolos -> lista de (salida, costo)"""
        # BFS con costo
        from collections import deque
        results=[]
        queue=deque()
        queue.append((self.inicial, 0, [], 0.0)) # estado, pos_input, output, costo
        while queue:
            q, i, out, costo = queue.popleft()
            if i==len(entrada) and q in self.finales:
                results.append((out,costo))
                if len(results)>=max_paths: break
                continue
            for a in self._idx.get(q, []):
                # epsilon entrada
                if a.entrada=="" or (i<len(entrada) and a.entrada==entrada[i]):
                    ni = i + (0 if a.entrada=="" else 1)
                    no = out + ([a.salida] if a.salida!="" else [])
                    queue.append((a.destino, ni, no, costo+a.peso))
        results.sort(key=lambda x:x[1])
        return results[:max_paths]

    def compose(self, otro: 'FST') -> 'FST':
        """Composición FST1 ∘ FST2"""
        comp=FST(f"{self.nombre}∘{otro.nombre}")
        comp.inicial=(self.inicial, otro.inicial)
        comp.add_estado(comp.inicial, inicial=True)
        if self.inicial in self.finales and otro.inicial in otro.finales:
            comp.finales.add(comp.inicial)
        # producto cartesiano simple
        for a1 in self.arcos:
            for a2 in otro.arcos:
                if a1.salida==a2.entrada or a1.salida=="" or a2.entrada=="":
                    q0=(a1.origen, a2.origen)
                    q1=(a1.destino, a2.destino)
                    comp.add_estado(q0); comp.add_estado(q1)
                    if a1.destino in self.finales and a2.destino in otro.finales:
                        comp.finales.add(q1)
                    salida = a2.salida if a2.salida!="" else a1.salida
                    entrada = a1.entrada
                    comp.add_arco(q0, entrada, salida, q1, a1.peso+a2.peso)
        return comp

    def to_dict(self):
        return {
            "nombre":self.nombre,
            "estados":list(self.estados),
            "inicial":self.inicial,
            "finales":list(self.finales),
            "arcos":[{"o":a.origen,"i":a.entrada,"out":a.salida,"d":a.destino,"w":a.peso} for a in self.arcos]
        }

# Fábrica MIU: ρ(x)>0 → fonema
def fst_rho_base():
    fst=FST("rho_base")
    fst.add_estado("q0", inicial=True)
    fst.add_estado("q1", final=True)
    # ρ(x)>0 -> rho
    fst.add_arco("q0","ρ","rho","q1")
    fst.add_arco("q0","rho","rho","q1")
    fst.add_arco("q0","conciencia","conciencia Φ_c=0.6829","q1", peso=0.1)
    fst.add_arco("q0","grace","GRACE 221R","q1")
    fst.add_arco("q0","miu","MIU ρ>0","q1")
    return fst

if __name__=="__main__":
    f=fst_rho_base()
    print(json.dumps(f.to_dict(), indent=2, ensure_ascii=False))
    print(f.transduce(["ρ"]))
    print(f.transduce(["conciencia"]))
