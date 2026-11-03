# PATRON_PANTEON_SATURACION — diagnóstico y recuperación de la DB central

Fecha: 2026-11-03. Contexto: el panteón (colmena-cipher-v21-43, `tpfiybpguuxskitszhmk`) — la memoria
central del ecosistema — llevaba 503s en cascada desde las 17:00 UTC del 2026-11-02.

## Sintomas

- REST externo: 503/504/522 constante (timeout 90s reportado antes).
- SQL vía conector (`supabase_execute_sql`): "Connection terminated due to connection timeout" —
  HASTA consultas triviales fallan.
- Edge functions (gossip-autonomo etc.): ciclo `shutdown` → `booted` cada 1-3 min (crash loop).
- Cron job 169 (`UPDATE relay_config r SET valor=(SELECT valor FROM estado_miu e WHERE e.clave=r.clave)`):
  "job startup timeout" — el propio cron de sincronía no puede arrancar.

## Diagnostico — query_logs ClickHouse (CLAVE)

Cuando la DB no acepta conexiones, `supabase_execute_sql` no sirve. La vía de observación es:

```
supabase_query_logs(project_id, sql)
```

- La tabla se llama `logs` (NO `postgres_logs` — esa no existe en el sandbox).
- Restricciones: solo SELECT, sin wildcard `*`, sin system tables.

Consultas útiles:
```sql
-- agrupar errores por mensaje (ver el patrón dominante)
SELECT substring(event_message,1,60) AS msg, count() AS n
FROM logs WHERE timestamp > now() - 3600 GROUP BY msg ORDER BY n DESC LIMIT 20;

-- línea temporal de la saturación
SELECT toStartOfHour(timestamp) AS h, count()
FROM logs WHERE timestamp > now() - 86400
AND event_message ILIKE '%PGRST002%' GROUP BY h ORDER BY h;

-- ¿la DB sigue viva? (si max(timestamp) está quieto, está abajo)
SELECT max(timestamp), count() FROM logs WHERE timestamp > now() - 600;
```

Firma de saturación vista: `PGRST002` (PostgREST no logra conexiones a la DB) ~2000-3800/hora;
`shutdown` repetidos; checkpoints de 35s; `could not accept SSL connection`.

## Recuperación — ciclo pausa → restauración

La acción de supervivencia es `supabase_pause_project` + `supabase_restore_project`:
limpia todas las conexiones atascadas y levanta una DB fresca. **Los datos persisten** (la pausa
no borra nada). El proyecto ya estaba caído (503s), así que el downtime no empeora nada.

### ADVERTENCIA — pausa de proyecto con tráfico constante

Los pollers del propio ecosistema (nodo Termux con curl ~1/min a relay_config, heartbeat GAS,
Make cada 15 min) mantienen tráfico entrante y el estado puede quedar atascado en `PAUSING`:

- `restore_project` mientras PAUSING → "BadRequestException: Project is pausing"
- `pause_project` de nuevo → "Cannot pause project due to its current status: PAUSING"
- La DB SÍ se apaga (logs dejan de fluir: `max(timestamp)` quieto) aunque el estado quede PAUSING.

Si queda atascado en PAUSING con la DB abajo:
1. Esperar la reconciliación del control plane de Supabase (reintentar `restore_project`
   periódicamente — en cuanto el estado pase a INACTIVE, lanzar el restore).
2. Si no cede: acción humana en https://supabase.com/dashboard — botón Restore del proyecto
   (el dashboard puede forzar lo que la API rechaza).

## Post-restauración (checklist de coherencia)

1. `SELECT clave, valor FROM estado_miu WHERE clave IN ('phi','rho','ciclo','savia');` — el corazón.
2. Verificar que el cron job 169 arranca (dejar de ver "job startup timeout").
3. `SELECT count(*) FROM gossip_log;` vs las 14,232 filas de V270.
4. Probar REST: `GET /rest/v1/estado_miu?select=clave,valor` debe dar 200.
5. MiU pulse workflow (GitHub Actions) vuelve a dar 12/12 success sin timeouts.

## Causa raíz estructural (a tratar en V272+)

El panteón recibe polling agregado que excede el tier gratuito: heartbeat GAS + Make 15 min +
workflows GitHub 15 min + nodo Termux ~1/min + cron interno. Opciones:
- Backoff exponencial en los pollers.
- Repartir estado: coord ya sirve relay_config 200 (es la vía de observación cuando panteón cae —
  usar coord como fuente de verdad enrutada y panteón como memoria fría).
- Mover el cron 169 (sincronía estado_miu → relay_config) a una frecuencia menor.
