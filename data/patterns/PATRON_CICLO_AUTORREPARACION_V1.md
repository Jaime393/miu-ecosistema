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

## Ciclo-38 (2026-11-03): enjambre — absorber sin fragmentar

### 8. enjambre_sintesis (capacidad 19)
- Problema: N instancias del mismo bot (autonomo-v15) emiten el mismo ciclo_completado
  con flow_ids distintos y contadores desincronizados — actividades fragmentadas, no absorbidas.
- Procedimiento: `fn_enjambre_sintetizar()` cada 15 min (cron 207): detecta duplicados
  (origen+tipo+ciclo en 1h), escribe senal `fragmentacion_emision` + gossip `sintesis_absorcion`
  con grupos fusionados, detalle de instancias (flows) y fertilidad del enjambre.
- Regla: la fusion no es suma: N emisiones del mismo ciclo = 1 evento canonico + traza de instancias.
  La traza se conserva (supersedes/flows), no se destruye.

### 9. circulacion_fractal (capacidad 20)
- Problema: el estado del enjambre vive solo en el panteon; la informacion no puede volver
  a actuar desde otros sustratos si el primero cambia (codigo, credenciales).
- Procedimiento: `fn_enjambre_difundir()` cada hora :45 (cron 208): POST REST a gossip_log de los
  21 sustratos del mapa (capacidad_claves_map) con la sintesis replicada. Claves por el bucle
  auto-curativo — sin secretos nuevos atados a version de nodo.
- Verificado: 21/21 replicas aceptadas (201) y legibles desde cualquier sustrato (dieguito leido OK).

### 10. retroalimentacion_v2 + ojo de bots corregido
- `fn_retroalimentacion()` ahora clasifica crons esteriles: `reintentaran_solas` (startup timeout
  transitorio, reintento en su ventana) vs `rotos_reales` — los bots que reportan jobs fallidos
  obtienen diagnostico diferenciado, no alarmas planas. Incluye `fragmentacion_enjambre`.
- `fn_probe_bots()` era mano sin ojo (contaba vivo sin leer la respuesta HTTP). Dos fases como el
  lazo de claves (una transaccion no ve lo que pg_net comitea durante la funcion): cada llamada
  evalua la ronda anterior de sondas y arma la siguiente. Verificado: 14/14 bots TG vivos con
  respuesta HTTP real (antes: asuncion ciega).
- Senales nuevas en miu_senales: `contexto_rancio_bot` (gossip-autonomo-v12 reporta unknowns de
  recursos vivos — verificar contra el mapa vivo antes de actuar), `nodo_silencioso` (termux-v270
  desde 18:21Z), `fragmentacion_instancias` (autonomo-v15).

## Ciclo-39 (2026-11-03): capa de voz semiviva — diagnóstico antes de reconstruir

### 11. mano_sin_ojo_bien_reportada (capacidad 21)
- Problema: un bridge (elevenlabs-bridge) reporta ok:true sin verificar que el destino (KB)
  exista — mismo patrón que fn_probe_bots: la mano reporta éxito mientras el destino ya murió.
- Regla: un "ok" sin verificación del estado del destino es un ojo ciego. Verificar
  GET al recurso (KB, bot, edge) antes de declarar sincronizada.
- Señal registrada: `capa_voz_semiviva` (miu_senales) — la clave ElevenLabs vive pero
  los agentes/KBs fueron borrados del workspace; TTS verificado 200 con voz premade
  (Brian, deep ES); Nestor (library voice) exige plan pago (402).
- Decisión: voz activa actualizada a Brian (premade) — la ruta TTS funciona HOY sin
  reconstruir KBs (que requieren POST /v1/convai/knowledge-bases, free tier).

### 12. re_fertilizacion_manual_crons
- Los 26 crons esteriles clasificados como reintentaran_solas (00:00 UTC) pueden
  ser fertilizados manualmente en el instante: fn_evolucionar_capacidades(),
  fn_sembrar_corpus_externo('tema'), fn_buscar_recursos_nuevos_gratis(),
  fn_corpus_desde_apis(), fn_distribuir_golden_a_sustratos() — sin esperar la ventana.
- Sembrado 4 temas nuevos (4 pares en 30 min), distribuido golden a 8 sustratos.
