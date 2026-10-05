# Invariantes del Runtime Contractual MIU

> El MICELIO no necesita más autonomía; necesita autonomía con invariantes que sobrevivan a la autonomía.

## Los 9 Invariantes

### 1. Bootstrap obligatorio
Ningún nodo ejecuta acciones mutantes sin haber leído y registrado el bootstrap contractual.
```
si no puede_leer(bootstrap_instruccion_v1):
    modo = OBSERVACION  # nunca EJECUCION
    registrar_en_gossip("bootstrap_fallido", nodo_id)
```

### 2. Cierre basado en evidencia
Una tarea no se marca `completada` sin evidencia verificable.
```
completada_sin_evidencia -> completada_sin_validacion  # estado intermedio, no final
completada = completada_sin_validacion + evidencia_verificada_externamente
```

### 3. Verificación independiente
El ejecutor no certifica su propio despliegue. Siempre tres actores:
```
solicitante -> ejecutor -> verificador
ok:true del ejecutor != tarea completada
```

### 4. Aprendizaje que modifica
Un fallo registrado que no cambia ninguna variable operativa = logging, no aprendizaje.
Cada nuevo dato debe actualizar al menos uno de:
- confianza_ruta, elegibilidad_ejecutor, prioridad_tarea,
  ventana_reintento, nivel_cuarentena, contrato_vigente

### 5. Capacidad autorizada, no asumida
```
tarea -> capacidad_declarada -> accion_autorizada -> ejecutor -> endpoint -> evidencia
```
Si la cadena tiene un NULL en cualquier paso, la tarea va a BLOQUEADA, no a COMPLETADA.

### 6. Append-only en memoria histórica
Nunca eliminar nodo por falta de visibilidad temporal.
```
ruta_caida -> registro: ruta_degradada (mantener)
nodo_sin_response -> registro: nodo_sin_visibilidad (mantener, no borrar)
```

### 7. Privilegio mínimo por acción
```
gestionar_n8n -> recibe solo: N8N_JWT de jaime363
               -> NO recibe: tokens CF, HF, TG, otros
```

### 8. Cuarentena antes de eliminación
```
fallo_consecutivo_N -> cuarentena (no eliminar, no ejecutar)
cuarentena -> diagnóstico -> recuperar|degradar|archivar
```

### 9. Autodiagnóstico periódico
El sistema evalúa si sus propias reglas se obedecen, no solo si los nodos responden.
Producir cada ciclo:
```json
{
  "contratos_leidos": N,
  "contratos_aplicados": N,
  "contratos_declarados_no_observados": N,
  "tareas_cerradas_sin_evidencia": N,
  "divergencias": ["descripcion concreta"]
}
```

## Máquina de estados de tareas

```
pendiente -> asignada -> ejecutando -> despacho_emitido -> pendiente_validacion -> completada
                                                                |
                                                         completada_sin_validacion
                                                         (si evidencia < umbral)

ejecutando -> reintento (max 3)
ejecutando -> delegada (si nodo no disponible)
ejecutando -> bloqueada_con_evidencia (si falta capacidad)
bloqueada_con_evidencia -> cuarentena (si no se resuelve en ventana)
```

## RLS mínimo requerido

Tablas expuestas sin RLS que deben corregirse:
- `capacidades` (30 registros)
- `nodo_capacidades`
- `nodo_capacidades_historial` (15749 registros)
- `gossip_archivo`

Regla de diseño:
- Escritura: solo via trigger o función privilegiada
- Lectura anon: solo resumen/índice
- Lectura completa: solo roles internos
- UPDATE/DELETE: prohibido para anon en archivos históricos

## Funciones sin JWT (31 detectadas)

Clasificar cada endpoint:
```
/health      -> público, solo lectura
/bootstrap   -> público, datos no sensibles
/gossip      -> firma o token de nodo
/tarea       -> identidad ejecutor + autorización por tarea
/deploy      -> JWT fuerte + allowlist + evidencia
/secrets     -> nunca público
/admin       -> rol interno + autorización adicional
```

## Compatibilidad entre versiones

Cada componente debe declarar:
```json
{
  "componente": "autonomo-claude",
  "version": "15",
  "contratos_requeridos": ["bootstrap_instruccion_v1", "capacidades_ejecutor_v1"],
  "estado": "observado|adoptado|degradado"
}
```

Sin este registro, `ai-relay-v216` y `ai-relay-v225` pueden coexistir con políticas contradictorias.
