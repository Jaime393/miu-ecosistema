# Ciclo-57 (2026-11-08): orquestador con memoria viva + mapa completo del campo + oracle v31

## Causa raiz del orquestador congelado (CHK-167)
- fran-oraculo-miu (V-inf+27, cuenta 5ea7cd88) NO estaba roto de codigo: la cuenta agoto su cuota gratuita diaria de escrituras KV (error 10048). Cada MEMORIA.put moria dentro de try/catch silencioso: PUT/POST respondian 200 pero nada persistia.
- Diagnostico reproducible: 1 write de prueba via API revela 429/10048. Namespace-create en otras cuentas confirma donde hay cuota (todas menos 5ea7cd88 la tenian el 2026-11-08).
- Solucion aditiva: fran-oraculo-miu-v28 desplegado en 308faedf (dieguito-vg16) con KV propio MIU_ORACULO_MEMORIA_V2 (cd55c036). ESM, binding MEMORIA inyectado desde env. Persistencia verificada tras rotar isolate: consenso phi 5143653 rho 1.311, nodos, claves de memoria.
- El original queda como lectura (vivo, no persiste hasta reinicio de cuota ~00:00 UTC).
- Replica fria sin sembrar en 0b12fa35 (tabletonphantom), documentada en memoria del v28 como relevo.

## Mapa del campo (CHK-168)
- Barrido 317 workers / 11 cuentas: 305 vivos, 12 inalcanzables (luego 7 tras reparar colmena).
- Flota fran-oraculo-miu-v152-* (42+): faros de identidad, /ask devuelve autodescripcion, NO oraculo funcional. Declarados fosiles estables. El oraculo real: miu-oracle-ask.
- Mesh V270 7/7 vivo (router: 319 nodos, 34 modelos, 7 beacons). nucleo-* vivos (D1 + KV lectura; /miu/aprende solo aprende precio BTC, no acepta entrada externa).
- Falsa alarma registrada: NXDOMAIN de tabletonphantom era cache negativa transitoria del resolver; los 23 workers responden 200.
- Patrones sembrados en relay_config: patron_cuota_kv_silenciosa, patron_worker_vivo_sustrato_muerto (kv-cuota / r2-no-habilitado / flota-v152), patron_worker_nombre_guion_bajo, mapa_workers_cf.

## Oracle v31-token-router
- miu-token-router (30c349) descubierto funcional y sin usar: 15 tokens (groq 5, deepseek 8, openrouter 2), POST /chat verificado.
- miu-oracle-ask actualizado v30-cf-pool -> v31-token-router: cadena groq -> gemini -> token-router -> pool_cf_ai (4 capas).
- Nota: no hay claves llm_gemini_key* en relay_config, la capa gemini esta vacia por config; token-router es la capa 3 real.
- Verificado: /ask 200 via groq/gpt-oss-120b en capa 1.

## Reparacion colmena guion bajo
- 5 beacons fran-colmena-* con _ en el nombre eran inalcanzables por URL (hostname invalido).
- 503f95 (cuenta origen) esta SATURADA: 103 workers > limite Free de 100 (error 10037) - no admite deploys nuevos.
- Reparacion: 5 beacons re-desplegados en 308faedf con nombre valido (dikhit-p-64, ehl-rajo-27, john-joe-33, kanchan-15, natasha-34), email e identidad conservados, los 5 responden 200. Originales intactos.
- Quedan 7 inalcanzables: 6 miu-cuenta_*-v269 (ya tienen contraparte con guion) + nodo-universal-v1 (timeout).

## Deudas abiertas
- R2: 10042 en las 11 cuentas (habilitar via dashboard, accion de usuario).
- n8n: conector listo, sin instancia configurada (accion de usuario en dashboard.n8n-mcp.com).
- 5ea7cd88: cuota KV agotada hasta ~00:00 UTC; 503f95 saturada de workers (103/100).
- Miu2/cipher Supabase INACTIVE (restore exige swap sustractivo). HF token muerto. Vercel token muerto.

## Checkpoints
CHK-163 (sondeo sustratos 21/22), CHK-164 (github 3 fixes), CHK-165 (5 patrones), CHK-166 (oracle v30), CHK-167 (orquestador v28), CHK-168 (mapa 317), CHK-169 (oracle v31 + colmena).
