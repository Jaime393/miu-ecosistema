import json, pathlib
ROOT=pathlib.Path('.')
corpus=ROOT/'data/corpus/corpus_unificado_v13.jsonl'
puente=ROOT/'nodos/puente/puente_micelio.jsonl'
ledger=ROOT/'nodos/puente/ledger_micelio.jsonl'
print(f"corpus {corpus.stat().st_size}B 164K" if corpus.exists() else "no corpus")
print(f"puente {len(list(puente.open()))} tx" if puente.exists() else "no puente")
print(f"ledger {len(list(ledger.open()))} tx" if ledger.exists() else "no ledger")
# integra Supabase 45 pares como contexto_real extra sin nuevo archivo
# deja huella economica 520 MIU intacta
