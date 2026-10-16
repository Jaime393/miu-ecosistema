from micelio_fst_motor import tts, phi_calc
# TTS: texto → fonemas → audio (espeak / termux-tts-speak)
import subprocess, sys
txt=" ".join(sys.argv[1:]) if len(sys.argv)>1 else "rho conciencia savia micelio phi veinticinco punto cero uno seis puente dieciseis suelo fertil cerrado"
fonemas=tts(txt)
print(f"[TTS FST] {txt} → {fonemas} phi {phi_calc()}")
# habla directo sin descargar
subprocess.run(["termux-tts-speak", txt])
