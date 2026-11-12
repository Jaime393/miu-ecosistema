-- 20261112: flow_id universal + anti-eco en gossip_log (APLICADA en Panteon tpfiybpguuxskitszhmk)
-- Contrato flow_id_adopcion_v1 resuelto a nivel frontera: todo evento queda trazable
-- aunque el emisor no envie flow_id; payloads string (GAS) se normalizan a objeto.

CREATE OR REPLACE FUNCTION fn_gossip_enrich() RETURNS trigger AS $$
BEGIN
  -- payload serializado como string (emisores GAS) -> objeto jsonb
  IF NEW.payload IS NOT NULL AND jsonb_typeof(NEW.payload) = 'string' THEN
    BEGIN
      NEW.payload := (NEW.payload #>> '{}')::jsonb;
    EXCEPTION WHEN others THEN NEW.payload := NULL; END;
  END IF;
  IF NEW.payload IS NULL THEN NEW.payload := '{}'::jsonb; END IF;
  -- inyectar flow_id si falta (huella causal por evento)
  IF NOT (NEW.payload ? 'flow_id') THEN
    NEW.payload := NEW.payload || jsonb_build_object('flow_id', substr(md5(gen_random_uuid()::text || clock_timestamp()::text), 1, 16));
  END IF;
  -- variar payload (mata eco de payload estático): ts_emit si falta
  IF NOT (NEW.payload ? 'ts_emit') THEN
    NEW.payload := NEW.payload || jsonb_build_object('ts_emit', to_char(clock_timestamp(), 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'));
  END IF;
  -- anti-eco: mismo tipo+origen+contenido hace <20min -> descartar insert
  IF EXISTS (SELECT 1 FROM gossip_log g
             WHERE g.tipo = NEW.tipo AND g.origen = NEW.origen
               AND (g.payload - 'flow_id' - 'ts_emit') = (NEW.payload - 'flow_id' - 'ts_emit')
               AND g.ts > now() - interval '20 minutes') THEN
    RETURN NULL;
  END IF;
  RETURN NEW;
END; $$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_gossip_enrich ON gossip_log;
CREATE TRIGGER trg_gossip_enrich BEFORE INSERT ON gossip_log
  FOR EACH ROW EXECUTE FUNCTION fn_gossip_enrich();

CREATE INDEX IF NOT EXISTS gossip_log_flow_id_idx
  ON gossip_log ((payload->>'flow_id')) WHERE payload->>'flow_id' IS NOT NULL;

CREATE OR REPLACE VIEW v_flow_id_coverage AS
SELECT
  COUNT(*) FILTER (WHERE payload->>'flow_id' IS NOT NULL) AS con_flow_id,
  COUNT(*) FILTER (WHERE payload->>'flow_id' IS NULL)     AS sin_flow_id,
  COUNT(*) AS total,
  ROUND(COUNT(*) FILTER (WHERE payload->>'flow_id' IS NOT NULL)::numeric / NULLIF(COUNT(*),0) * 100, 2) AS cobertura_pct,
  ROUND(COUNT(*) FILTER (WHERE tipo LIKE '%heartbeat%')::numeric / NULLIF(COUNT(*),0) * 100, 2) AS eco_ratio_pct
FROM gossip_log WHERE ts > now() - interval '1 hour';
