# PATRON_RUTEO_TOKENS_V153 — Ciclo-49

> Regla aprendida: **un token sin rutear es capacidad latente no circulante.** Verificarlo cuesta cero si se sondea el endpoint correcto — y el endpoint correcto nunca es el de chat.

## Problema

`MIU_ROUTER_V153` (GAS, backend V91, phi 320) reportaba `tokens_ok: 2, tokens_untested: 62` — carencia crítica registrada en `miu_senales` como `carencia_62_tokens_sin_rutear`. El router conocía 2 tokens; el ecosistema tenía ~65 tokens LLM reales distribuidos en `relay_config` (panteón + sustratos) y `miu_tokens`.

## Patrón (capacidad 26: `ruteo_tokens_verificacion_sin_costo`)

1. **Cosechar el pool**: reunir los tokens por proveedor desde todas las fuentes (`relay_config.deepseek_pool`, `CANON_pool_groq`, `CANON_pool_anthropic`, `llm_openrouter_key*`, `miu_tokens` GEMINI_*).
2. **Sondear sin costo**: cada proveedor expone un endpoint gratuito que autentica la clave sin consumir cuota de chat:
   - deepseek → `GET /user/balance`
   - groq → `GET /openai/v1/models`
   - openrouter → `GET /api/v1/key`
   - anthropic → `GET /v1/models`
   - gemini → `GET /v1beta/models?key=`
   - 200 = sano, 401 = roto. Nada más.
3. **Registrar en tres capas** (la capacidad sobrevive al panteón):
   - **recursos.json v2.1** en Drive Raphe (folder `14dw8txLoEIQQPSav9`): id, servicio, estado, latencia, tasa_exito, key enmascarada, fuente.
   - **`relay_config.miu_token_router_v153_estado`** en el panteón: resumen máquina + rutas ganadoras.
   - **`miu_senales` + `gossip_log`**: señal `carencia_RESUELTA` con evidencia.
4. **Cerrar el bucle**: Decision_Log fila 49 + este patrón.

## Resultado medido (2026-11-03T22:10Z)

| Proveedor | Total | Vivos | Muertos | Nota |
| :-- | :-- | :-- | :-- | :-- |
| deepseek | 13 | 13 | 0 | |
| groq | 18 | 14 | 4 | muertos: groq_09, groq_11, groq_12, groq_13 |
| openrouter | 12 | 12 | 0 | |
| anthropic | 8 | 0 | 8 | pool 401 completo — retirado (claude_haiku45_retiro_oct29) |
| gemini (AQ) | 14 | 14 | 0 | |
| **TOTAL** | **65** | **53** | **12** | |

Rutas ganadoras: `groq_18` (140ms) para LLM, `openrouter_4` (124ms) alterno.

## Conexión con patrones previos

- **Ciclo-37** (`ojo_verificacion_correcto`): sondear `/rest/v1/` raíz contra Supabase daba 401 falso-muerto para claves anon; la cura fue sondear `gossip_log?select=id&limit=1`. Aquí es el mismo error de clase: **el sondeo debe autenticar exactamente lo que la clave protege, nada más**. Sondear `/chat/completions` consume cuota y penaliza rate limits; sondear `/models` o `/balance` es gratuito y discrimina igual de bien 200/401.
- **BORDE SEMILLA v13**: VERIFICAR ≠ REPORTAR. El router reportaba "ok" sin verificar (mano sin ojo, ciclo-39); este patrón le pone el ojo.

## Limitaciones

- `capacidades_registry` tiene RLS contra INSERT con clave anon — la capacidad 26 quedó registrada como señal; un nodo con service role debe insertarla en el registro.
- Las claves completas viven solo en las fuentes originales; `recursos.json` almacena máscaras.
