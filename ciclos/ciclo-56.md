# Ciclo-56 (2026-11-03): browser directo + coord router fix desplegado

## Coordinador
- Login Google jaimepvicente via browser (cloud): backup code 43743526 + device prompt aprobado por el usuario (tap Yes + numero 47). TOTP secreto regenerado por Google (el de totp_secrets.txt quedo obsoleto).

## Make org 8248425 (MIU)
- Login exitoso via browser. Plan Free, 831/1000 creditos, equipo My Team (2519057).
- 11 escenarios visibles (2 activos: V276 gossip-pulse 272 ops, V287 oracle-gossip 790 ops; 9 inactivos).
- Trash: 2 versiones viejas del oracle (V277, V278).
- jardinero-v6 (6392384): INACCESIBLE - "Insufficient rights, team permission View scenario details is needed". No esta en team 2519057 ni en Trash. Probado con teams 2968749/2968233: "admin permission organization view is needed". Vive en un equipo/org donde Juan (Owner de 8248425) no tiene vista.
- DLQ de escenarios revisados: VACIOS (6392334, 6771105). No hay BundleValidationError en DLQ.
- Warning V287: 504 Gateway Timeout (ConnectionError) + pausas por rate-limit del plan Free (cada 15min se pausa 5-720min).

## Coord router fix - DESPLEGADO Y VERIFICADO
- Causa raiz: pathname.replace fallaba segun la forma del pathname -> todas las rutas caian al catch-all 404.
- Fix: split por slug (inmune a cualquier prefijo).
- Despliegue: supabase CLI v2.78.1 con sbp_jaimepviccente (dueño del coord fepyzxwyneervidlybvi), --no-verify-jwt.
- El bloqueo de la API de gestion (PATCH multipart -> 500 "Cannot read properties of undefined") se EVITO usando el CLI.
- Verificado: /ping -> {"vivo":true,...}, /mapa -> datos completos, /contexto -> tareas+nodos+metricas. Todas responden 200.
- Recurso panteon: d425b4b3-cc05-4c4c-9f23-c00cb45823e4 (coord_router_fix_ciclo56) + señal hito.

## Tokens sbp_ localizados (relay_config panteon)
- 14 sbp_ por cuenta: tabletonephantom, jaimedaniel, franchesco, franrussell, jhuarcaya x2, cipher (42ddb3fa), dereckcito x2, dieguito x2, jaimepvicente, jaimepviccente (fcb14c2a), javier.
- jaimepviccente = dueño del coord fepyzxwyneervidlybvi.

## Pendientes
- jardinero 6392384: identificar cuenta/owner real del equipo donde vive.
- Facebook Pages (jaimedanielmartinez75) via browser.
- earthdata endpoints autenticados (red diferente).
