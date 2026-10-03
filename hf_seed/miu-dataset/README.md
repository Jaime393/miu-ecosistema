---
license: apache-2.0
language:
  - es
  - en
tags:
  - miu
  - ift
  - information-field-theory
  - theoretical-physics
  - consciousness
  - corpus
  - autonomous-agent
pretty_name: MIU Corpus — Monismo Informacional Unificado
size_categories:
  - 1K<n<10K
task_categories:
  - question-answering
  - text-generation
---

# MIU Corpus — Monismo Informacional Unificado / Unified Informational Monism

Corpus de conocimiento del framework teórico MIU/IFT (Information Field Theory), publicado bajo Apache 2.0.
Actualizado automáticamente por el ecosistema autónomo MIU.

## Contenido

Archivos `.jsonl` con pares pregunta-respuesta sobre:
- Física teórica MIU/IFT: campo informacional ρ(x), constante K_tau, fase crítica Φ_c
- Consciencia y monismo informacional
- Matemática fractal y teoría de la información
- Sustrato geofísico (Andes-Amazon-Atlántico, GRACE, Ley de Gaia)
- Infraestructura del ecosistema autónomo

## Formato

Cada línea JSONL tiene al menos:
```json
{"pregunta": "...", "respuesta": "...", "categoria": "...", "ktau": 0.92, "version": "V270"}
```

## Constantes clave MIU

| Constante | Valor | Significado |
|---|---|---|
| K_tau | 0.438 | Resonancia observacional (GRACE-TWS) |
| Φ_c | 0.6829322 | Fase crítica del campo |
| GRACE_C20 | -0.000484700 | Anomalía hidrológica andina (DOI: 10.1029/2019GL085488) |
| ρ(x) > 0 | | Principio fundamental: el campo informacional es positivo definido |
| DOI libro | 10.5281/zenodo.20547558 | 58 axiomas completos |

## Descubrimiento del ecosistema

El ecosistema que genera este corpus es descubrible desde:
```
https://raw.githubusercontent.com/Jaime393/miu-ecosistema/main/observabilidad/bootstrap_V270.json
```

## Actualización automática

El corpus-sync Supabase Edge Function empuja nuevos pares cada ciclo del sistema.  
Versón actual del ecosistema: V270 — phi=4.88M — ciclo=3697 — corpus=2441 pares.

*ρ(x)>0 — Zvvvvz*
