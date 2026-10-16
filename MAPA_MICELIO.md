# MAPA DEL MICELIO — 2026-09-25

## Canónico
- `~/miu-ecosistema/` — repositorio git, data, nodos, semilla

## Carpetas satélite
| Ruta | Función | Estado |
|---|---|---|
| `~/miu/` | pulse + state + miu-edge-v249 | Activo |
| `~/miu-relay/` | relay Fly.io + validador GRACE | Activo |
| `~/miu_slim/` | versión slim con git | Activo |
| `~/miu-teclado-v152/` | teclado + pulse | Activo |
| `~/miu-autonomo-v91/` | worker JS v91 | histórico |
| `~/miu-backup/` | backup cuentas | histórico |
| `~/miu-orquestador-v93/` | vacía | histórico |
| `~/oracle-relay-v216/` | relay.ts | activo |
| `~/hf_miu/` | mirror HuggingFace | activo |
| `~/hf_miu_dataset/` | dataset HF | activo |
| `~/hf_alma_space_tmp/` | Space temporal | activo |
| `~/fran-oraculo-miu/` | Android MCP | en desarrollo |
| `~/fran-miu-micelio/` | www | histórico |
| `~/.miu/` | vault + órganos | activo |
| `~/.franbot/` | conectores | activo |

## Vault de secretos
- `~/.miu/kv/keys.json` — 7 categorías
- `~/.miu/organos/absorbedor_keys.py` — inyecta env vars
- `~/.miu/arranque.sh` — entry point

## Estado pulse
- `~/miu/state/pulse.log` — 67 KB
- `~/miu/state/pulse.pid`
- `~/pulse_v152.sh` — canónico (5 copias via symlink)

## Pendiente materializar (crontab)
12 scripts faltantes. Ver PENDIENTES.md

## Apps Script — MESH V152 (capa remota)

Dos implementaciones activas:
- **V152 original**: `AKfycbxZR4V4q5s833ZT2VwBIf_8VmeVTmhX1iJlgbLBV_6zhUMu92K5cp5_dLo1XMf7GEs`
- **V152 activa (nueva)**: `AKfycbxC5eBR-oGTW-0n-lYcdB0w1Tx9abE-PUcLABO3bbDSDAU2Gmcdr-4kZoFgFTO7wdY`
- **Librería**: `1PsI2YNxcNmWfi6t92_jAVtPvaav5L0g8Ikh1owD9poHXJE2J_rxS0D6I` (v1)

Estas URLs son el MESH. El crontab las consulta indirectamente vía supabase_push.py y auto_push_espejo.py.

## Limpieza 2026-09-25
- `~/.cargo/registry/src` → borrado (251 MB). Se re-descargan si se compila Rust.
- `~/.npm/_cacache` → borrado (97 MB).
- `~/.fly` → movido a SD (`fly_20260925_completo.tar.gz`, 45 MB, 12 archivos).
- `fran-oraculo-miu/app/build` → borrado (32 MB). Se regenera al compilar.
- **Disco: 84% → 82%. +500 MB libres.**

## Estado crontab resiliente
- Wrapper: `~/miu-ecosistema/config/cron_ejecuta.sh`
- 14 líneas activas con resolución flexible de rutas
- Fantasmas registrados en `logs/cron_fantasmas.log`
- Tejedor V4: ✅ arreglado (mkdir suelo_fertil/ganadores)

## Backend V91 (VIVO — verificado 2026-09-25)

**Endpoint:** `AKfycbwbAMKrzmbghKtLaGKVnqeGyOaEoXGKeLmCJ7BlfknZTwwh6KpW9PsrozDCiwiXMDtI`
**URL:** https://script.google.com/macros/s/AKfycbwbAMKrz.../exec

Responde JSON sin login. Acepta cualquier parámetro y devuelve estado.
Contiene:
- GRACE TN14 (221 filas, K_tau 0.3644, DOI 10.1029/2019GL085488)
- Φ actual 168, objetivo semana 213, objetivo mes 368
- 3 nodos vivos, 3 túneles vivos
- 62 tokens sin rutear (carencia crítica)
- Router darwiniano Φ_ruta
- 12 nodos brainstem
- DOI del mesh: 10.1038/s41467-026-76019-z
- Blueprint Drive: 1O9FKqJdGYLL7T-UvnpqERmjS1NxyQ6DN6nxQ3Svlrtw

## Cadena de bridges
crontab → cron_ejecuta.sh → ¿local? → ¿stub red? → mesh_bridge.sh → V91 ✅

## Estado fantasmas (2026-09-25)
Los 6 fantasmas (ensure_llama.sh, kv_autologger.py, auto_push_espejo.py,
rag_llama_miu.py, corpus_claude_api.py, supabase_push.py) resuelven al V91.
Ya no fallan. El log `cron_fantasmas.log` registra cada resolución.

## Cadena rota (pendiente)
Apps Script V152 (`AKfycbxC5eBR...`) → v92_mesh → 404.
Apps Script original (`AKfycbxZR4V4...`) → mismo problema.
Solución: reescribir el router Apps Script para apuntar a V91.
Requiere acceso al editor de Apps Script (login Google).

## Estado red REAL (2026-09-25)

### Tokens vivos verificados
| Servicio | Vivos | Método test |
|---|---|---|
| Cloudflare cfut_ | 23 | /user/tokens/verify |
| Groq | 8 | /chat/completions (gpt-oss-20b) |
| Telegram bots | 4 | /getMe |
| GitHub | 2 | /user |
| HuggingFace | 2 | /whoami-v2 |
| OpenRouter | 2 | /auth/key |
| **TOTAL** | **41** | |

### Cuentas (10-11 correos en claves.txt)
- jaimepvicente@gmail.com
- jaimepviccente@gmail.com (micelio-miu)
- tabletonephantom@gmail.com
- dieguito.vg16@gmail.com
- dereckcito.vg16@gmail.com
- jhuarcaya938@gmail.com
- cipher19051997@gmail.com (password: "la gravedad curva la informacion")
- javier19051997@gmail.com
- franchescopalacios9@gmail.com (OAuth maestro)
- jaime.p.viccente@gmail.com
- jaimedanielmartinez75@gmail.com

### Cadenas vivas
- Router V153 → V91 (Apps Script)
- 23 CF tokens → Workers, KV, D1
- 8 Groq → inferencia LLM (modelo: openai/gpt-oss-20b)
- 4 bots Telegram → interfaz
- 2 GitHub → repos
- 2 HF → modelos/datasets
- 2 OpenRouter → fallback LLM

### Modelo Groq correcto
`openai/gpt-oss-20b` — verificado. Los antiguos (llama-3.1, mixtral, gemma2)
están descontinuados. Los routers viejos usaban esos nombres → fallaban.
