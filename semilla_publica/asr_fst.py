from micelio_fst_motor import asr
# ASR: fonemas → texto (vía Vosk / termux-speech-to-text)
import subprocess, json
# captura audio 3s y transduce
print("[ASR FST] escuchando 3s...")
r=subprocess.run(["termux-speech-to-text"], capture_output=True, text=True)
phon=r.stdout.strip()
print(f"[ASR raw] {phon}")
print(f"[ASR FST] → {asr(phon)}")
