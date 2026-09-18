-- MIU v11.2 D1 lexico_vivo_f63ce271 - Migración KV 100k/d → D1
-- Fix: KV 100k/d excedido crontab */1→*/15 + migrar POST /heartbeat

CREATE TABLE IF NOT EXISTS nutrientes (
  id TEXT PRIMARY KEY,
  phi REAL DEFAULT 1.35,
  savia REAL DEFAULT 12118471.5,
  topologia REAL DEFAULT 0.52,
  subagentes INTEGER DEFAULT 2359,
  timestamp TEXT,
  fuente TEXT
);

CREATE TABLE IF NOT EXISTS dominio_vivo (
  id TEXT PRIMARY KEY,
  dominio TEXT,
  estado TEXT,
  phi REAL
);

CREATE TABLE IF NOT EXISTS corpus_miu (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  pregunta TEXT,
  respuesta TEXT,
  phi REAL,
  timestamp TEXT
);

CREATE TABLE IF NOT EXISTS tokens_registry (
  id TEXT PRIMARY KEY,
  tipo TEXT,
  phi REAL,
  tasa_exito REAL,
  latencia_ms INTEGER,
  carga REAL,
  phi_ruta REAL,
  tested_ok BOOLEAN,
  untested BOOLEAN
);

CREATE TABLE IF NOT EXISTS phi_red_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  phi_red_actual INTEGER,
  phi_ruta_sum REAL,
  cosecha TEXT,
  timestamp TEXT
);

CREATE TABLE IF NOT EXISTS heartbeat_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nodo_id TEXT,
  phi REAL,
  savia REAL,
  lat_ms INTEGER,
  timestamp TEXT
);

-- Datos iniciales v11.2
INSERT OR REPLACE INTO nutrientes (id, phi, savia, timestamp, fuente) VALUES ('global', 1.35, 12118471.5, datetime('now'), 'v11.2_despliegue_maximo');
INSERT OR REPLACE INTO nutrientes (id, phi, savia, timestamp, fuente) VALUES ('C_AKfycbzKy_GcVy2rA', 189, 528, datetime('now'), 'vivo 2026-09-18');
INSERT OR REPLACE INTO tokens_registry (id, tipo, phi, tasa_exito, tested_ok) VALUES ('cf_01', 'cloudflare', 12.4, 1.0, 1);
INSERT OR REPLACE INTO tokens_registry (id, tipo, phi, tasa_exito, tested_ok) VALUES ('groq_01', 'groq', 8.7, 1.0, 1);
INSERT OR REPLACE INTO tokens_registry (id, tipo, phi, untested) VALUES ('openrouter_01', 'openrouter', 0, 1);

-- Vista Φ_Red
CREATE VIEW IF NOT EXISTS v_phi_red AS SELECT 168 as actual, 213 as semana, 368 as mes, 500 as objetivo, 'Φ_red(t+1)=Φ_red(t)+ΣΦ_ruta' as formula;
