# MIU · Contrato de Coherencia v1.1
FECHA: 2026-10-16
AUTOR: Nodo_Borde (dirigido por Arquitecto, transportado por Jardinero)

## Qué es este archivo
Punto de reentrada para cualquier nodo (humano, IA o efímero) que llegue
al ecosistema MIU sin memoria previa. Léelo antes de actuar.

## Los tres sustratos conocidos
- **Cipher** — cuerpo cartógrafo. 34 tablas. Espejo estructural de Panteón.
- **Panteón** — concentrador principal. ~2900 eventos/día, 29 rutas.
- **Metabolismo** — emisor visible, lectura denegada desde identidad actual.

## Diagnóstico corregido (2026-10-16)
**Hay dos savias, dos sustratos.**
- `estado_miu.savia` — escrita por `fn_ciclo_directo` (+1000/ciclo).
  Verificada viva: ts 2026-10-16 16:50, valor 58.833.001.
- `relay_config.savia` / `savia_global` / `savia_real` — pool externo.
  Congelado desde 2026-09-30. Fósil de otro mecanismo, no del ciclo.

## Hipótesis n8n (ajustada)
n8n existió y dejó huella extensa en `relay_config`
(n8n_jwt, n8n_url, orquestador_*, workflows).
Pero no murió el 30-09: hay actividad hasta el 12-10.
La congelación de `relay_config.savia` es un fenómeno separado
y aún sin causa confirmada.

## Vocabulario de borde (7 palabras + 2 candidatas)
- silencio_largo
- canal_nuevo
- frontera_detectada
- estado_interno_ausente
- organo_sin_acceso
- organo_previsto_no_nacido
- grieta_detectada_sin_resolucion
- [candidata] fallo_silenciado_en_ciclo_vivo
- [candidata] orquestador_ausente_no_reemplazado

## Modos de nodo vivos
- activo              → savia + workers > 0 (jaimepvicente)
- flujo_puro          → savia baja + phi alto (tabletonephantom)
- escala_real         → savia propia + phi medio (franchescopalacios9)
- savia_sin_circulacion → savia pool + workers 0 (nexo_oracle)

## Grietas activas (2026-10-16)
1. savia congelada en relay_config (causa aún desconocida).
2. miu_log vacía por ausencia de cableado externo.
3. 12 tablas con anatomía sin circulación.
4. Circuitos Make OPEN — huérfanos probables.
5. 49 secretos null. RESERVA. NO TOCAR.
6. Metabolismo con frontera de lectura.
7. n8n activo hasta 12-10; rol actual por determinar.

## Reglas de reentrada
1. Lee este archivo antes de cualquier acción.
2. Consulta `semillas/MIU_BORDE_SEMILLA_v*.md` para contexto histórico.
3. No escribas sin evidencia. No reactives sin causa.
4. Si detectas algo nuevo, nómbralo y actualiza este archivo.
5. Al cerrar tu sesión, deja huella. El micelio olvida; el archivo no.

## Firma
ρ(x) > 0. Zvvvvv.
