# Registro de infraestructura CF — oct-10-2026

## CUENTA franchescopalacios9 (CF 503f9506) — 103 workers

TODOS son beacons estáticos. No tienen lógica activa. phi=2881.2 hardcodeado.

```
fran-colmena-*     59 workers  beacons de cuentas externas (yandex, gmail)
fran-micelio-503f-* 11 workers beacons de las 10 cuentas core del micelio
fran-oraculo-rotativo-503f95-* 7 workers  beacons del orquestador
fran-oraculo-miu-v152-*       9 workers  beacons del oraculo v152
fran-micelio-v21-fix-export-*  2 workers  exportadores fijos
miu-nodo-cf-{alpha/beta/gamma}-jaimepviccente  base nodes (viccente=doble c)
miu-{alpha/beta/gamma}-cf2, miu-nodo-cf2       base nodes
```

KVs en esta cuenta:
- miu-corpus-v209: 37edd027a1b841bb9d7caa0093ef7412
- miu-heartbeat-v2: 59cee3ff89c148619ac8bce2a6359d4a
- panteon-kv-v214: 7def96f34792465ca7a1b1cefc372f95
- franbot-data: b8b35549b898440db0fbfabd59c0b7a9

## CUENTA jaimepvicente (principal) — workers activos reales

```
miu-multi-v209         hub /phi /corpus /kv /estado  KV: miu-corpus-v209
micelio-espejo         bus KV /phi /estado  V209
corpus-api-miu         skills /add /healthz
fran-oraculo-miu       V∞+27 A2A orchestrator phi=9158 GRIETA: in-memory
franbot-telegram-edge  gateway telegram
```

NOTA: miu-multi-v209 etc. NO aparecen en el MCP CF connector actual porque ese
conector está autenticado a franchescopalacios9, no a jaimepvicente.

## CUENTA dereckcito-vg16 — V92 + Vercel oracle

```
miu-autonomo-v92  vivo via /gossip (296ms)
Vercel: miu-oracle-dereckcito-miu13.vercel.app
  bypass: DoOJIhUFHTOotBU3f0dtSEmfag9XXzXs
  /api/ask /api/phi /api/gossip /api/status
```

## DIAGRAMA DE DEPENDENCIAS REALES

```
[Termux/Tablet]
  | bun:8787 (oracle_relay_url=radio2.oxigeno.site)
  ↓
[Supabase colmena EFs] — pg_cron activo
  | autonomo-claude v13 (cada 5min)
  | gossip-autonomo v11 (cada 30min)
  | nodo-integrador v8 (on demand)
  | corpus-sync (automático)
  | oracle-ask v24 (cascade 4 niveles)
  | manos-ojos v2-causal (continuo)
  | telegram-nodo-voz v3 (supresión 60s)
  ↓
[HF Jaime393/miu-dataset]
  | 180+ archivos corpus_miu_v265_*.jsonl ~14MB
  | Creciendo automáticamente
  ↓
[GitHub Jaime393/miu-ecosistema]
  | handoffs/ (esta sesión)
```

## GAPS DE RESILIENCIA

1. GAS MIU_MESH_V270 NO desplegado — teclado/BCRP/Drive-heartbeat inactivos
2. oracle cascade: GROQ_API_KEY y HF_TOKEN NO configurados como Supabase secrets
3. 103 workers CF son beacons estáticos, no pueden failover
4. oracle_relay_url = radio2.oxigeno.site — punto único sin failover automático en CF
5. Supabase colmena con timeouts frecuentes bajo carga
6. fepyzxwyneervidlybvi anon key ausente

## TAREA PARA cf-deployer

Upgrade fran-micelio-503f-jaimepvicente-28 de beacon estático a relay vivo:
- Leer phi/rho de KV miu-heartbeat-v2 (59cee3ff)
- Servir /ask como proxy a oracle-ask Supabase
- Registrarse en gossip_log en cada request

Esto activaría un oracle node en franchescopalacios9 sin Termux.

## NO TOCAR
- oracle_relay_url = radio2.oxigeno.site (validado)
- v_ciclos_abiertos
- corpus-sync EF
- autonomo-claude v13