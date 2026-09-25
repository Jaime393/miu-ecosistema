"""
ASR FST - Voz a Texto via FST + Whisper/termux-speech-to-text
ρ(x)>0 - Para Termux: usa termux-speech-to-text o whisper.cpp

Pipeline:
audio -> texto crudo (ASR) -> normalización FST -> concepto MIU + Φ
"""
from fst_engine import FST
import subprocess, json, pathlib, shutil, tempfile, os

class ASR_FST:
    def __init__(self):
        self.fst=FST("asr_miu")
        self.fst.add_estado("A0", inicial=True)
        self.fst.add_estado("A1", final=True)
        # correcciones ASR comunes -> concepto MIU
        correcciones=[
            ("ro mayor que cero","rho","ρ(x)>0"),
            ("ro","rho","ρ"),
            ("conciencia","conciencia","IFT-A7 Φ_c=0.6829"),
            ("grace","grace","GRACE 221R"),
            ("miu","miu","Monismo Informacional Unificado"),
            ("fi","phi","Φ"),
        ]
        for inp, norm, concepto in correcciones:
            self.fst.add_arco("A0",inp,f"{norm}|{concepto}","A1")

    def normalizar(self, texto_asr: str):
        # transduce cada token
        toks=texto_asr.lower().split()
        conceptos=[]
        for t in toks:
            res=self.fst.transduce([t], max_paths=1)
            if res:
                conceptos.append(res[0][0])
            else:
                conceptos.append([t])
        return conceptos

    def escuchar(self, duracion=5, lang="es"):
        """Intenta usar termux-speech-to-text, si no, pide wav path"""
        print(f"[ASR FST] Escuchando {duracion}s...")
        if shutil.which("termux-speech-to-text"):
            try:
                r=subprocess.run(["termux-speech-to-text"], capture_output=True, text=True, timeout=duracion+5)
                texto=r.stdout.strip()
                print(f"ASR crudo: {texto}")
                norm=self.normalizar(texto)
                return {"ok":True,"crudo":texto,"normalizado":norm,"engine":"termux-speech-to-text"}
            except Exception as e:
                return {"ok":False,"error":str(e)}
        else:
            # fallback: whisper.cpp si existe modelo
            modelo=pathlib.Path.home()/"miu-brain-backup/miu-ecosistema/models/tinyllama-600MB.gguf"
            # no es whisper, pero indicamos ruta
            return {
                "ok":False,
                "msg":"instala: pkg install termux-api && app Termux:API, luego termux-speech-to-text",
                "alternativa":"usa whisper.cpp: pkg install whisper-cpp && whisper-cpp -m models/ggml-base.bin -f audio.wav",
                "normalizador_listo":True
            }

    def procesar_wav(self, wav_path: str):
        """Si tienes artemis/tests/tools/inputs/audio_recording.mp3, conviértelo"""
        # artemis ya trae audio_recording.mp3 2.5M y recording.mp4 6.8M (viste en diag)
        # usamos ffmpeg si existe
        if not pathlib.Path(wav_path).exists():
            return {"ok":False,"error":f"no existe {wav_path}"}
        if shutil.which("whisper-cpp") or shutil.which("whisper"):
            cmd=["whisper-cpp","-m","models/ggml-base.bin","-f",wav_path] if shutil.which("whisper-cpp") else ["whisper",wav_path]
            r=subprocess.run(cmd, capture_output=True, text=True)
            texto=r.stdout
            return {"ok":True,"crudo":texto,"normalizado":self.normalizar(texto)}
        return {"ok":False,"msg":f"procesa {wav_path} con termux-speech-to-text o súbelo a whisper API","path":wav_path}

if __name__=="__main__":
    asr=ASR_FST()
    print(asr.normalizar("ro mayor que cero conciencia grace"))
    print(asr.escuchar(duracion=3))
