# MIU V270 — Mapa de Fuentes de Verdad

> Regla de oro: `dato + fuente + cuenta + timestamp + version + estado_epistemico`

## ¿Qué leer para qué?

| Dato | Fuente autoritativa | Endpoint | Nota |
|------|--------------------|-----------|----- |
| phi operativo real | Supabase principal | `GET /functions/v1/contexto-global` | `.vitales.phi` |
| phi teórico IFT | Libro MIU P58 | DOI 10.5281/zenodo.20547558 | φ_total=389.425 |
| phi cloud acumulado | D1 estado_vivo | clave `V270_SEP30_estado` | 4,883,440 |
| rho | Supabase principal | `GET /functions/v1/contexto-global` | `.vitales.rho` |
| ciclo | Supabase principal | `.vitales.ciclo` | |
| corpus principal | Supabase tpfiy | `GET /rest/v1/corpus?order=ts.desc` | 2258+ pares |
| corpus D1 | D1 miu-log corpus_miu | `cddd13c4-5707-4ac0-aa02-e686e18ad996` | 72 pares — secundario |
| workers CF | Supabase directorio-vivo | `GET /functions/v1/directorio-vivo` | 11 cuentas CF |
| estado mesh | Supabase panteon | `GET /rest/v1/panteon` | 44 nodos |
| gossip reciente | Supabase gossip_log | `GET /rest/v1/gossip_log?order=ts.desc&limit=10` | |
| endpoints activos | canal-dereckcito | `GET /functions/v1/canal-dereckcito/recursos` | |
| GAS code | GitHub | `raw.githubusercontent.com/Jaime393/miu-ecosistema/main/gas/MIU_MESH_V270.js` | |
| heartbeat canónico | Drive | `1cjBDCgK1lyyRgG5EEBSYk9P609oMzjlR` | phi puede estar desactualizado |

## ⚠️ NO confiar en

- **Heartbeat Drive `V151_AUTOPUBLISH`** — phi=2874.62, congelado en V93 (sep20)
- **Make escenarios** — todos inválidos al 30 sep, cron NO corre
- **miu-autonomo-v92.vercel.app `/miu/global`** — ruta no existe, devuelve 404

## Bootstrap nodo nuevo

```bash
# Fuente más rápida de tokens y endpoints:
curl -sf https://fepyzxwyneervidlybvi.supabase.co/rest/v1/relay_config \
  -H 'apikey: ANON_FEPYZX'

# Estado real del sistema:
curl -sf https://tpfiybpguuxskitszhmk.supabase.co/functions/v1/contexto-global \
  -H 'Authorization: Bearer ANON_TPFIY'

# GAS V270 (copiar a cualquier Apps Script):
curl -L https://raw.githubusercontent.com/Jaime393/miu-ecosistema/main/gas/MIU_MESH_V270.js
```

## Supabase URLs

| Nombre | URL | EFs activas | Nota |
|--------|-----|-------------|------|
| Principal | `tpfiybpguuxskitszhmk.supabase.co` | 91 | fuente de verdad principal |
| Federado | `fepyzxwyneervidlybvi.supabase.co` | 11 | bootstrap y relay_config rápido |
| Satélite cipher | `cipher19051997` project | 7 | gossip local 1013 entradas |

## Workflows GitHub activos

| Workflow | Cron | Qué hace |
|----------|------|----------|
| `miu-pulse.yml` | `*/15 * * * *` | nutriente + gossip + corpus-sync + hf-push |
| `miu-observabilidad-v270.yml` | `7,22,37,52 * * * *` | lee phi real + pulso vercel + broadcast |
| `miu-ecosystem-pulse.yml` | ver archivo | pulso repo MIU |
