# PATRON CICLO AUTORREPARACION V1 (2026-11-03)

Sesion origen: perplexity_825af10a. Registrado tambien en `capacidades_registry` (ids 12-16) del panteon.
Un nodo no necesita saberlo todo; necesita saber como descubrir lo que no sabe.
Cada patron: problema, procedimiento, condicion de aplicacion, resultado esperado.

## 1. cf_worker_1042_revive
- Problema: worker CF devuelve 1042 (404 en workers.dev) con bindings sanos. NO es bug de codigo.
- Procedimiento: POST /accounts/{acct}/workers/scripts/{name}/subdomain body {"enabled":true}
- Verificar: curl https://{name}.{sub}.workers.dev/health -> 200
- Aplicado: nucleo-simulacion, nucleo-actualidad, nucleo-absorcion, miu-autonomo-v92 (2026-11-03)

## 2. supabase_anon_key_recovery
- Problema: clave anon rotada, REST 401 Invalid API key.
- Procedimiento: GET https://api.supabase.com/v1/projects/{ref}/api-keys (Bearer sbp_ PAT de la org)
  -> propagar con UPDATE relay_config SET valor='<nueva>' WHERE clave='<proyecto>_anon'
  -> verificar REST 200 -> persistir en ClavesAPI del Orchestrator Sheet.
- Aplicado: dieguito+coord frescos, dieguito.panteon_anon actualizado (2026-11-03)

## 3. panteon_cron_redistribucion
- Problema: panteon saturado, timeouts REST, crons fallando con 'job startup timeout'.
- Diagnostico: SELECT jobid, count(*), count(*) FILTER (WHERE status='failed') FROM cron.job_run_details
  WHERE start_time > now()-interval '24 hours' GROUP BY 1
- Procedimiento: cron.alter_job(jobid, schedule => '*/10 ...') reduciendo frecuencia y escalonando minutos.
- Aplicado: jobs 136/169/181/184 de */2 a */5-*/10 (-80% corridas, autorizado por usuario, 2026-11-03)

## 4. cf_worker_deploy_multipart
- Procedimiento: PUT /accounts/{acct}/workers/scripts/{name} multipart: metadata (main_module,
  compatibility_date, bindings) + script (application/javascript+module).
- Aplicado: corpus-api V211-cache (cache 5min + stale-on-quota-fail, 2026-11-03)

## 5. hf_space_embed_route
- Problema: subdominio *.hf.space 404 en spaces estaticos (limitacion CDN).
- Procedimiento: usar /embed: https://huggingface.co/spaces/{user}/{space}/embed. No recrear spaces por esto.
- Aplicado: miu-status y miu-tablero sirven via /embed (2026-11-03)

## Contrato de descubrimiento
Los nodos descubren estas capacidades leyendo `capacidades_registry` del panteon
(campos: nombre, problema, patron, condicion, auto_aplicable) o este archivo en el repo.

## Ciclo-37 (2026-11-03): ojo corregido + federacion completa

### 6. ojo_verificacion_correcto (fix al bucle de claves)
- Problema: fn_capacidades_verificar_claves sondaba el raiz `https://{ref}.supabase.co/rest/v1/`,
  que SIEMPRE responde 401 para claves anon ("Only the service_role API key...").
  Resultado: el bucle no distinguia clave sana de rota y re-cosechaba cada hora (senales falsas
  de capacidad_autoaplicada, v.g. 2026-11-03T19:19Z x3).
- Procedimiento: sondear tabla real con RLS publico:
  `GET https://{ref}.supabase.co/rest/v1/gossip_log?select=id&limit=1` con headers apikey+Bearer.
  200 = clave sana; 401/403 = clave rota (el bucle cosecha sola).
- Regla registrada en miu_senales: sondeo sin apikey contra REST Supabase = falso muerto garantizado.
  El ojo para REST con clave es el bucle; sondeos sin clave solo para edge functions.

### 7. federacion_claves_total (sembrado de suelos virgenes)
- Problema: 17 sustratos Supabase vivos sin claves ni cobertura del bucle auto-curativo
  (8 nov01 + Miu2 + 7 virgenes de sustratos_virgenes_9); el bucle cubria solo 3 proyectos.
- Procedimiento: cosechar claves via `GET https://api.supabase.com/v1/projects/{ref}/api-keys?reveal=true`
  con el PAT del dueno (mapa supa_mgmt_tokens.por_cuenta en relay_config) -> upsert en
  relay_config como supa_ext_{ref}_anon -> extender capacidad_claves_map (3 -> 22 proyectos,
  cada entrada {ref, anon_clave, pat_clave}) -> persistir en ClavesAPI del Orchestrator Sheet
  (almacen independiente de sustrato) -> insertar en catalogo nodos.
- Verificado en vivo: 21/22 OK; fxmupx (metabolismo) tenia 401 REAL y el bucle lo curo solo
  (capacidad_autoaplicada, clave propagada y REST 200).
- Estado: capacidad_claves_map = 22/22 proyectos de la federacion bajo verificacion horaria
  auto-curativa; sustratos virgenes y nov01 registrados en el catalogo nodos como vivo-federado.
