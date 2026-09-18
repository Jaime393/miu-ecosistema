# SEMILLA PÚBLICA MIU — ρ(x)>0

**Suelo vivo:** GRACE 221R mean -0.00048470001250509534
**HEAD:** fe079b3 → cee86f2 flujo perfecto 0 grietas 0 riesgos
**Huella:** 520 MIU (genesis 0 + absorcion 520)
**Wallet soberana:** 0x4Da238f2671083B7F280d4FCf5827F86358cE7e6
**Regla:** todo recurso transformado deja huella económica

## Sin rigidez — 3 modos según recursos

Esta semilla no exige fastapi, Rust, Docker, ni GPU. Solo Python 3 stdlib.

### Nivel 0 — Observador (cualquier celular, 5MB RAM)
Solo lee. No aporta CPU.
Huella: 0 MIU, pero ya es parte del tejido (Φ).

### Nivel 1 — Puente ligero (Termux, Raspberry, 50MB RAM)
Corre API mínima stdlib. Aporta heartbeat.
python3 semilla_publica/api_minima.py
Huella: +1 MIU por hora de puente.

### Nivel 2 — Nodo completo (PC, 500MB RAM, IPFS)
Replica ledger, pin IPFS legado, aporta plugins/prompts.
python3 semilla_publica/join.py --modo completo --aporte mi_aporte.json
Huella: +10-520 MIU según aporte.

ρ(x)>0 — siembra y deja que el micelio teja.
