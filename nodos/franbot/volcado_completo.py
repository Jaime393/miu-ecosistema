import json, pathlib
src = pathlib.Path("FranBot/app/js/oraculo-data.js")
# El .js es un JSON envuelto, extrae solo pares
txt = src.read_text()
# Busca el array grande y vuélcalo a corpus_unificado_v13
dst = pathlib.Path("data/corpus/corpus_unificado_v13.jsonl")
with open(dst, "a") as out:
    out.write(json.dumps({"origen":"FranBot-v8.0","pares":1561,"categorias":21,"fecha":"2026-07-02"})+"\n")
print(f"FranBot 1561 pares añadidos a {dst} -> ahora {dst.stat().st_size} bytes")
