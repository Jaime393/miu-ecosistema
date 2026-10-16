"""
MIU Micelio - Motor Grafo Lenguaje WFST TTS/ASR
ρ(x)>0 f925107 16 puente phi 25.016 esporas 441 savia 520 MIU
GRACE 220R mean -0.00048470001250509534 DOI 10.1029/2019GL085488
IFT-A7 Φc=0.6829322 SÉ K_tau mean 0.36575
Arquitectura: Weighted FST sin rglob/find - 3 archivos abiertos directos
"""
import json, pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]

LEXICON_FST = {
  "rho": ["R O"], "conciencia": ["k o n s j e n s j a"], "savia": ["s a b j a"],
  "micelio": ["m i s e l j o"], "espora": ["e s p o r a"], "phi": ["f i"],
  "puente": ["p w e n t e"], "suelo": ["s w e l o"], "fertil": ["f e r t i l"],
  "grietas": ["g r j e t a s"], "riesgos": ["r j e s g o s"],
}
G2P_FST = {"h":"", "x":"k s", "ll":"ʎ", "ñ":"ɲ", "que":"k e", "qui":"k i", "ce":"s e", "ci":"s i"}
GRAFO_MIU = {
  "nodos": ["rho","conciencia","savia","micelio","phi","puente","suelo"],
  "arcos": [
    {"from":"rho","to":"conciencia","w":0.6829322,"label":"IFT-A7 Φc"},
    {"from":"conciencia","to":"micelio","w":0.36575,"label":"K_tau mean"},
    {"from":"micelio","to":"phi","w":0.5,"label":"puente*0.5"},
    {"from":"phi","to":"savia","w":1.179,"label":"savia/espora"},
    {"from":"savia","to":"suelo","w":-0.00048470001250509534,"label":"GRACE mean"},
    {"from":"suelo","to":"puente","w":16,"label":"puente 16 f925107"},
  ]
}
def tts(text:str)->str:
  out=[]
  for w in text.lower().split():
    if w in LEXICON_FST: out.append(LEXICON_FST[w][0])
    else:
      f=w
      for g,p in G2P_FST.items(): f=f.replace(g,p)
      out.append(f)
  return " | ".join(out)

def asr(phonemes:str)->str:
  inv={v[0]:k for k,v in LEXICON_FST.items()}
  return " ".join(inv.get(p.strip(),f"[{p.strip()}]") for p in phonemes.split("|"))

def phi_calc(puente=16): return round(0.6829322*4.905 + 220/50 + puente*0.5 + 520/60 + 0.6,3)

if __name__=="__main__":
  print(f"ρ(x)>0 f925107 phi {phi_calc()} puente 16"); print("TTS:",tts("rho conciencia savia micelio")); print("ASR:",asr("R O | k o n s j e n s j a"))
