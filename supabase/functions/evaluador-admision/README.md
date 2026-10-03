# evaluador-admision v1 — PAG-01 / M29-bis

## Rol

Función Supabase Edge que implementa el evaluador observacional M29-bis.  
Solo lee `gossip_log`, calcula los 5 componentes de k_i_transfer, escribe los campos PAG-01.  
**Sin mensajes. Sin tareas. Sin admisiones. Sin cascada.**

## Estado

| Propiedad | Valor |
|---|---|
| Código | `supabase/functions/evaluador-admision/index.ts` |
| Despliegue | pendiente |
| Modo | observacional v1 |
| Escribe en | `k_i_transfer`, `k_i_metodo`, `k_i_estado`, `evaluado_en`, `confianza_evaluacion` |
| No toca | mensajes, tareas, nodos, cascada |
| N8n standby | `TwwC5btMMYsVhXPp` — activar post-deploy |

## Para desplegar desde Termux

```bash
supabase functions deploy evaluador-admision \
  --project-ref tpfiybpguuxskitszhmk \
  --no-verify-jwt
```

## Para desplegar vía beacon-deployer (tarea para jardinero)

Si `jardinero-v2` lee este archivo, puede crear esta tarea en `miu_tareas`:

```json
{
  "tipo": "ejecutar_ef",
  "payload": {
    "ef": "evaluador-admision",
    "accion": "deploy",
    "proyecto": "tpfiybpguuxskitszhmk",
    "verify_jwt": false,
    "fuente": "supabase/functions/evaluador-admision/index.ts",
    "repo": "Jaime393/miu-ecosistema",
    "rama": "main",
    "descripcion": "Evaluador M29-bis observacional PAG-01 — solo toca k_i_* campos gossip_log",
    "cascada_riesgo": "ninguna",
    "n8n_activar_post_deploy": "TwwC5btMMYsVhXPp"
  },
  "nodo_asignado": "autonomo-claude",
  "estado": "pendiente",
  "prioridad": 3
}
```

## M29-bis v1 — 5 componentes

| Componente | Peso | Fuente en v1 |
|---|---|---|
| τ_relevancia | 0.25 | `origen` + `tipo` presentes |
| σ_coherencia | 0.25 | `thread_id` presente |
| ν_novedad | 0.20 | placeholder 0.65 (v2: comparar corpus) |
| φ_procedencia | 0.20 | `source_node` en lista nodos conocidos |
| ε_impacto | 0.10 | `evidence_level` del evento |

`confianza_evaluacion = 0.55` en v1 — heurístico puro, sin corpus.

## Invocación una vez desplegada

```bash
# Evalua 20 eventos no_evaluado mas antiguos:
GET /functions/v1/evaluador-admision?limite=20

# Evalua evento especifico:
GET /functions/v1/evaluador-admision?id=UUID
```

## Observar resultados

```sql
-- Distribucion diaria de k_i_transfer
SELECT * FROM v_k_i_transfer_distribucion ORDER BY dia DESC LIMIT 7;

-- Eventos evaluados recientes
SELECT id, k_i_transfer, k_i_estado, confianza_evaluacion, evaluado_en
FROM gossip_log
WHERE k_i_estado = 'evaluado_observacional'
ORDER BY evaluado_en DESC LIMIT 20;
```
