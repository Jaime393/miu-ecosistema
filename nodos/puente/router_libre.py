import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
MAN = json.load(open(ROOT / "MANIFIESTO_VIVO.json"))

def usar_recurso_gratis(path_candidato):
    p = pathlib.Path(path_candidato)
    if p.exists() and p.stat().st_size > 0:
        return p
    return None

recurso = (
    usar_recurso_gratis(MAN["GRACE_TN14"]) or
    usar_recurso_gratis(MAN["corpus_unificado_v13"]) or
    usar_recurso_gratis("FranBot/app/js/oraculo-data.js") or
    usar_recurso_gratis("/storage/emulated/0/Download/miu_corpus_unified_v12.jsonl")
)
print(f"recurso vivo usado: {recurso} — no dependencia, solo ruta")
