# evaluador-admision v1 — PAG-01 / M29-bis

## Rol

Funcion Supabase Edge que implementa el evaluador observacional M29-bis.  
Solo lee `gossip_log`, calcula los 5 componentes de k_i_transfer, y escribe los campos PAG-01.  
**Sin mensajes. Sin tareas. Sin admisiones. Sin cascada.**

## Estado

| Propiedad | Valor |
|---|---|
| Codigo | listo en repo |
| Despliegue | pendiente — NO auto-desplegado |
| Modo | observacional v1 |
| Escribe en | `k_i_transfer`, `k_i_metodo`, `k_i_estado`, `evaluado_en`, `confianza_evaluacion` |
| No toca | mensajes, tareas, nodos, admission_gate, cascada |

## Para desplegar

```bash
# Desde Termux con SUPABASE_ACCESS_TOKEN en relay_config:
supabase functions deploy evaluador-admision \
  --project-ref tpfiybpguuxskitszhmk \
  --no-verify-jwt
```

## M29-bis v1 — 5 componentes

| Componente | Peso | Fuente en v1 |
|---|---|---|
| τ_relevancia | 0.25 | origen + tipo presentes |
| σ_coherencia | 0.25 | thread_id presente |
| ν_novedad | 0.20 | placeholder 0.65 (v2: comparar corpus) |
| φ_procedencia | 0.20 | source_node en lista nodos conocidos |
| ε_impacto | 0.10 | evidence_level del evento |

`confianza_evaluacion = 0.55` — deliberadamente baja en v1 (heurístico sin corpus).

## Invocacion

```bash
# Evalua 10 eventos no_evaluado mas antiguos:
GET /functions/v1/evaluador-admision?limite=10

# Evalua un evento especifico:
GET /functions/v1/evaluador-admision?id=UUID
```

## Condicion para v2

- Conectar a corpus para ν_novedad real
- Elevar confianza_evaluacion cuando k_i_estado pase a `evaluado_completo`
- Activar admision solo cuando k_i_transfer < umbral configurable
