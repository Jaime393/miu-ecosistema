"""
TTS FST - Texto a Voz via FST + eSpeak/pespeak fallback
ρ(x)>0 - Para Termux: pkg install espeak

Pipeline:
texto -> normalización FST -> fonemas -> WAV via espeak
Si no hay espeak, devuelve fonemas + comando para reproducir
"""
from fst_engine import FST
import subprocess, pathlib, json, shutil

class TTS_FST:
    def __init__(self):
        self.fst=FST("tts_miu")
        self.fst.add_estado("T0", inicial=True)
        self.fst.add_estado("T1", final=True)
        # reglas de normalización simples ES
        reglas=[
            ("rho","ʁo","rho"),
            ("conciencia","konsˈθjen.sja Φ","conciencia"),
            ("grace","ɡɾas","GRACE"),
            ("miu","miu ρ>0","MIU"),
            ("Φ_c","fi sub ce 0.68","phi_c"),
        ]
        for inp, fon, out in reglas:
            self.fst.add_arco("T0",inp,f"{fon}|{out}","T1")

    def texto_a_fonemas(self, texto: str):
        toks=texto.lower().split()
        fonemas=[]
        for t in toks:
            res=self.fst.transduce([t], max_paths=1)
            if res:
                fonemas.append(res[0][0])
            else:
                fonemas.append([t])
        return fonemas

    def hablar(self, texto: str, lang="es-la", velocidad=175):
        fonemas=self.texto_a_fonemas(texto)
        print(f"[TTS FST] {texto} -> {fonemas}")
        if shutil.which("espeak"):
            # espeak -v es-la -s 175 "texto"
            try:
                subprocess.run(["espeak","-v",lang,"-s",str(velocidad),texto], check=False)
                return {"ok":True,"fonemas":fonemas,"engine":"espeak"}
            except Exception as e:
                return {"ok":False,"error":str(e),"fonemas":fonemas}
        elif shutil.which("termux-tts-speak"):
            subprocess.run(["termux-tts-speak",texto])
            return {"ok":True,"fonemas":fonemas,"engine":"termux-tts"}
        else:
            return {"ok":False,"fonemas":fonemas,"msg":"instala: pkg install espeak && termux-tts-speak","comando":f"espeak -v {lang} -s {velocidad} \"{texto}\""}

if __name__=="__main__":
    tts=TTS_FST()
    print(tts.texto_a_fonemas("rho conciencia grace"))
    tts.hablar("rho equis mayor que cero, conciencia phi ce cero punto seis ocho, grace doscientos veintiuno")
