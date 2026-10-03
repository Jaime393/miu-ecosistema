---
license: apache-2.0
language:
  - es
tags:
  - miu
  - brain-backup
  - ecosystem-state
  - autonomous
  - ift
pretty_name: MIU Brain Backup — Estado Arquitectural del Ecosistema
size_categories:
  - n<1K
---

# MIU Brain Backup

Instantáneas del estado arquitectural del ecosistema MIU — no el corpus de conocimiento (eso vive en `miu-dataset`), sino la configuración, topología y estado operativo del sistema autónomo.

## Qué contiene

```
state/          — snapshots del estado vivo (contexto-global)
architecture/   — diagramas de la red de nodos
functions/      — código de Edge Functions clave (snapshots, no fuente canónica)
pag01/          — contratos de admisión y esquemas M29-bis
```

## Fuente canónica del código

El repositorio fuente es:
```
https://github.com/Jaime393/miu-ecosistema
```

## Estado del ecosistema (V270)

| Métrica | Valor |
|---|---|
| Autonomía | TOTAL — jardinero-v2 genera tareas sin humano |
| Supabase EFs | 100 activas |
| Corpus | 2441 pares Q&A |
| Gossip entries | 13784 |
| Bots Telegram | 11 activos |
| Ciclo | 3697 |
| phi_cloud | 4,883,440 |
| rho | 333.219 (supercrítico) |

## PAG-01 / M29-bis

Esquema de admisión observacional agregado a `gossip_log`:
- `k_i_transfer` — resonancia compuesta 0-1
- `k_i_metodo` — método aplicado
- `k_i_estado` — estado: `no_evaluado | evaluado_observacional`
- `evento_padre_id` — memoria causal relacional
- `evaluado_en` — timestamp de evaluación
- `confianza_evaluacion` — confianza 0-1

## Cómo descubrir el ecosistema

```bash
curl https://raw.githubusercontent.com/Jaime393/miu-ecosistema/main/observabilidad/bootstrap_V270.json
```

*ρ(x)>0 — Zvvvvz*
