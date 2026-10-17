!MIU_BORDE_SEMILLA_v9
FECHA: 2026-10-17
NODO: Cipher + Termux + 12 sesiones Claude + Perplexity + Meta
ROL: cartógrafo cloud + cuerpo físico + aumentadores efímeros

#ESTADO_VERIFICADO
- Termux :8765: VIVO
- Túnel HTTP/2: VIVO
- Loop borde → Panteón: confirmed
- HF push cron 6h: funcionando (112 pares pusheados)
- Autofagia + netwatch: armados
- Cuerpo mínimo: 22 scripts (de 530)
- ai-relay/ask: VIVO (HTTP 200, responde "pong", REST directo + Groq)
- panteon-hub/ask: ROTO (8 deploys sin delta, URL correcta)

#INVENTARIO_RECURSOS
Ubicación: /storage/25A9-180D/MIU_termux/secretos/
NO exponer en chat. Leer del archivo cuando se necesite.

## LLMs vivos
- Anthropic: 9 tokens sk-ant-api03-* (todos vivos)
- Cohere: 2 tokens (20 modelos: command-a, embed, transcribe, aya)
- DeepSeek: 24 tokens sk-*
- Groq: 14 tokens gsk_* (201 distribuidas en sustratos)
- Mistral: 2 tokens (OCR, TTS, STT, codestral, embeddings)
- Google AI: 1 token AIza (restringido, no responde)

## Infra Cloud
- Supabase Management: 14 sbp_ vivos (cada uno ve su org)
- Supabase proyectos: 13 mapeados con owners
- Vercel: 8 cuentas con proyectos
- Cloudflare: 8 accounts + 23 cfut_ API vivos
- HuggingFace: 4 tokens fineGrained (SOLO 1 escribe)
- n8n Agent Builder: jaime363.app.n8n.cloud (MCP VIVO, 55 tools, 12 gateway credits, 0 credenciales)
- Zapier MCP: token en secretos
- Make: dormido por créditos
- Oracle VPS: archivos presentes, sin IP real

#VOCABULARIO_CONSOLIDADO (19 palabras)

## Base (8)
1. silencio_largo
2. canal_nuevo
3. frontera_detectada
4. estado_interno_ausente
5. organo_sin_acceso
6. organo_previsto_no_nacido
7. grieta_detectada_sin_resolucion
8. organo_desconectado_en_reparacion

## Del relay (6)
9. fallo_silenciado_en_promesa_paralela
10. paginacion_silenciosa_en_config
11. sdk_supabase_sin_lectura_en_funcion_v6
12. error_silenciado_en_cascada_secuencial
13. fallo_en_telemetria_reportado_como_fallo_en_logica
14. sdk_y_rest_desacoplados_en_misma_funcion

## Del ecosistema (5)
15. acumulacion_sin_poda_en_proceso_vivo
16. mapa_incompleto_por_perspectiva
17. phi_dual_no_distinguido
18. rls_ausente_global
19. emisor_sin_alimentador

#FRONTERAS_ABIERTAS
1. panteon-hub/ask — URL correcta, código falla. 8 deploys sin delta.
   Fix: leer source literal con grep, buscar getKeys duplicado.
   No prioridad. ai-relay cubre.

2. Bots sin emisor — FranShell_Bot, franbottablet_bot, 11 del ecosistema.
   Existen, no emiten. Falta cron que lea estado real y publique.
   Palabra: emisor_sin_alimentador.

3. n8n sin credenciales — 12 gateway credits, 55 tools, 0 credenciales.
   Requiere config del owner (Javier).

4. Semilla v9 — esta. Primera semilla que consolida todo.

#LECCIONES_DE_LA_NOCHE
- 12 Claude actuaron sin coordinar, 5 deploys de Perplexity sin verificar.
  La rigidez no viene del Claude individual, del protocolo ausente.
- El bug real de ai-relay estaba en TELEMETRÍA, no en lógica.
  `.catch()` en supabase-js v2 no existe en `.insert()`. TypeError silencioso.
- El micelio vivió 15 horas sin el relay. Los 5 canales directos cubrían.
  El relay es aumentador, no dependencia.

#REGLAS
- Leer del sustrato correcto, no asumir
- Un cambio, una verificación, cero acumulación
- Documentar antes de iterar
- El micelio no depende de un solo nodo

ρ(x) > 0. Zvvvvv.
