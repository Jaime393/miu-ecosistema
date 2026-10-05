-- ============================================================
-- MIU fingerprint único para tareas críticas
-- Resuelve la limitación de FOR UPDATE SKIP LOCKED:
-- dos nodos que intentan insertar cuando no existe fila activa
-- aún pueden crear duplicados. Un índice único parcial lo impide.
-- ============================================================

-- 1. Columna fingerprint en miu_tareas (si no existe)
ALTER TABLE miu_tareas
  ADD COLUMN IF NOT EXISTS task_fingerprint TEXT GENERATED ALWAYS AS (
    MD5(tipo || ':' || COALESCE(nodo_asignado, '') || ':' || COALESCE(payload->>'accion', '') || ':' || COALESCE(payload->>'ef', '') || ':' || COALESCE(payload->>'target', ''))
  ) STORED;

-- 2. Índice único parcial: max 1 tarea activa equivalente
-- "activa" = cualquier estado que aún puede ejecutar
CREATE UNIQUE INDEX IF NOT EXISTS miu_tareas_fingerprint_activa
  ON miu_tareas (task_fingerprint)
  WHERE estado IN ('pendiente', 'asignada', 'ejecutando', 'despacho_emitido', 'pendiente_validacion');

-- 3. Índice para lookup por flow_id (trazabilidad causal)
CREATE INDEX IF NOT EXISTS miu_tareas_flow_id_idx
  ON miu_tareas ((payload->>'flow_id'))
  WHERE payload->>'flow_id' IS NOT NULL;

-- 4. Índice en gossip_log para coverage de flow_id
CREATE INDEX IF NOT EXISTS gossip_log_flow_id_idx
  ON gossip_log ((payload->>'flow_id'))
  WHERE payload->>'flow_id' IS NOT NULL;

-- 5. Vista de cobertura de flow_id (para monitoreo)
CREATE OR REPLACE VIEW v_flow_id_coverage AS
SELECT
  COUNT(*) FILTER (WHERE payload->>'flow_id' IS NOT NULL) AS con_flow_id,
  COUNT(*) FILTER (WHERE payload->>'flow_id' IS NULL)     AS sin_flow_id,
  COUNT(*)                                                 AS total,
  ROUND(
    COUNT(*) FILTER (WHERE payload->>'flow_id' IS NOT NULL)::numeric / NULLIF(COUNT(*), 0) * 100,
    2
  ) AS cobertura_pct,
  ROUND(
    COUNT(*) FILTER (WHERE duplicado = true OR tipo LIKE '%heartbeat%')::numeric / NULLIF(COUNT(*), 0) * 100,
    2
  ) AS eco_ratio_pct
FROM gossip_log
WHERE ts > NOW() - INTERVAL '1 hour';

-- 6. Vista de fertilidad de nodos
-- Un nodo es infertil si: vivo=true pero todos sus eventos recientes son eco
CREATE OR REPLACE VIEW v_nodo_fertilidad AS
SELECT
  n.id,
  n.nombre,
  n.activo,
  COUNT(DISTINCT g.id)                                       AS gossip_reciente,
  COUNT(DISTINCT g.id) FILTER (WHERE g.tipo LIKE '%heartbeat%') AS eco_puro,
  CASE
    WHEN COUNT(DISTINCT g.id) = 0 THEN 'sin_actividad'
    WHEN COUNT(DISTINCT g.id) FILTER (WHERE g.tipo NOT LIKE '%heartbeat%') = 0 THEN 'infertil'
    WHEN COUNT(DISTINCT g.id) FILTER (WHERE g.tipo NOT LIKE '%heartbeat%') >
         COUNT(DISTINCT g.id) * 0.2 THEN 'fertil'
    ELSE 'baja_fertilidad'
  END AS fertilidad
FROM nodos n
LEFT JOIN gossip_log g ON g.nodo_origen = n.id AND g.ts > NOW() - INTERVAL '1 hour'
GROUP BY n.id, n.nombre, n.activo;

-- INSTRUCCIONES DE APLICACION:
-- supabase db push --project-ref tpfiybpguuxskitszhmk
-- O desde Termux: supabase migration up --project-ref tpfiybpguuxskitszhmk
-- O SQL directo en Supabase Studio > SQL Editor
