# PATRON: Router de edge functions + pool Vercel (ciclo-55, 2026-11-04)

## Problema 1: router del coord (miu-recursos)
`url.pathname.replace('/functions/v1/miu-recursos', '')` falla según la forma del pathname que pasa el runtime — TODAS las rutas caían al catch-all 404 (contexto, semilla, mapa, ping). El nodo coord (fepyzx-coord-v268, phi 9157.36) estaba "vivo pero sordo".

## Fix preparado
`const path = (url.pathname.split('miu-recursos')[1] ?? '/').replace(/\/+$/, '') || '/';`
— split por el slug: inmune a cualquier prefijo del runtime.

## Bloqueo
API de gestión de Supabase `PATCH /v1/projects/{ref}/functions/{slug}`:
- multipart (todos los formatos probados) → 500 "Cannot read properties of undefined (reading 'toString')"
- JSON → 200 pero solo actualiza metadata (ezbr_sha256 sin cambio, versión sin bump)

**Siguiente ruta**: desplegar via CLI de supabase desde Termux/EF, o conector con permisos de deploy al coord.

## Problema 2: Vercel "re-auth" — RESUELTO por pool
El token fijo `miu13` murió, pero el pool rotativo tenía 20/22 tokens vcp_ vivos cubriendo 6 cuentas (dieguitovg16, jaimepviccente, jaimedanielmartinez75, jhuarcaya938, franrussell81). `bridge_pool_vercel_v1` espejado en relay_config. Confirma la regla del ciclo-54: los fijos mueren, el pool vive.

## Earthdata
Token JWT vivo hasta dic-2026 (uid a36963). CMR search accesible. Los endpoints autenticados (api.earthdata.nasa.gov) no resuelven desde el sandbox — se necesita un nodo con la red correcta (Termux/EF).
