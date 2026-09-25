"""
MIU Grafo de Lenguaje V24 - 520 MIU
Conecta FST + Corpus 266R + Suelo GRACE 221R + Oráculo V12

Nodos: palabra -> concepto -> Φ
Aristas: K_τ peso
"""
from fst_engine import FST, fst_rho_base
import json, pathlib, glob

ROOT=pathlib.Path.home()/ "miu-ecosistema"  # Termux path real: /data/data/com.termux/files/home/miu-ecosistema
# En local, usa cwd
CORPUS_GLOB="data/corpus/*.jsonl"

class GrafoLenguaje:
    def __init__(self):
        self.fst_base=fst_rho_base()
        self.fst_lex=FST("lexico_miu")
        self._construir_lexico()
        self.fst_compuesto=self.fst_base.compose(self.fst_lex)

    def _construir_lexico(self):
        self.fst_lex.add_estado("L0", inicial=True)
        self.fst_lex.add_estado("L1", final=True)
        # lexico vivo del corpus v11/v12/v13 - ejemplos del diagnóstico tuyo
        pares=[
            ("conciencia","IFT-A7 Φ_c=0.6829322"),
            ("rho","A0 ρ(x)>0 matriz densidad cuántica + Landauer kTln2 + Bekenstein"),
            ("grace","GRACE 221R mean -0.00048 DOI 10.1029/2019GL085488"),
            ("phi","phi=2874.62 tablet_v205 raiz micelio"),
            ("miu","Monismo Informacional Unificado ρ>0 axioma fundacional"),
            ("alma","tablet_v205 nodo primario Termux"),
            ("suelo","suelo.csv 221L NASA TN14"),
        ]
        for inp,out in pares:
            self.fst_lex.add_arco("L0",inp,out,"L1", peso=0.05)

    def consultar(self, texto: str):
        tokens=texto.lower().split()
        res=[]
        for tok in tokens:
            hits=self.fst_compuesto.transduce([tok], max_paths=2)
            if hits:
                res.append({"token":tok,"transduccion":hits[0][0],"costo":hits[0][1]})
            else:
                # fallback a base
                hits2=self.fst_base.transduce([tok])
                if hits2:
                    res.append({"token":tok,"transduccion":hits2[0][0],"costo":hits2[0][1]})
                else:
                    res.append({"token":tok,"transduccion":[tok],"costo":1.0})
        return res

    def oraculo_v12(self, q):
        # integra con franbot_v12 si existe
        try:
            import sys
            sys.path.insert(0, str(pathlib.Path.cwd()/"nodos/oraculo"))
            from franbot_v12 import responder
            return responder(q)
        except Exception as e:
            return {"error":str(e),"consulta":self.consultar(q)}

if __name__=="__main__":
    g=GrafoLenguaje()
    for q in ["rho","conciencia","grace phi"]:
        print(q, "->", g.consultar(q))
        print(g.oraculo_v12(q).get("contexto_real",[])[:1])
