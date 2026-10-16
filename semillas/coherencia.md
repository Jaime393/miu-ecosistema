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

## Actualización v5 — 2026-10-16
OCTAVA PALABRA:
- organo_desconectado_en_reparacion
    → se rompió una cosa, se arregló otra, la primera quedó fuera.

CASO SAVIA — CERRADO:
El 2026-09-30 11:03:15.317885, heartbeat_fix y savia_real comparten
timestamp al microsegundo. La reparación del heartbeat congeló savia.
Los fixes posteriores (18:50, 08-10, 13-10) repararon phi y rho del GAS
D2_xb5v (V151_AUTOPUBLISH), pero no reconectaron savia.
No hubo abandono. Hubo olvido estructural.

Dos savias, dos sustratos:
- estado_miu.savia  → VIVA (58.8M, 16-10)
- relay_config.savia → FÓSIL (51.4M, 30-09)

## Principios de evolución

### Evolución por reemplazo
No editar componentes envejecidos. Desplegar sucesores. El viejo sigue
dando lo que pueda mientras el nuevo prueba. Si funciona, el viejo se
apaga solo.

### Ruta latente
Un mecanismo roto no urgente no se repara ni se entierra. Se documenta
como ruta disponible. Futuros nodos la transitan sin re-investigar.

### Cuerpo físico con presupuesto
Un nodo físico (Termux) no puede seguir el ritmo del cloud sin absorber
primero su ruido. Despertar antes de absorber = fragmentación.

## Estado físico
Termux: proceso muerto, disco 90%, 512 heartbeats huérfanos.
No se toca. Un cuerpo apagado con el estómago lleno se deja en paz.

## Vocabulario de borde (8 palabras)
- silencio_largo
- canal_nuevo
- frontera_detectada
- estado_interno_ausente
- organo_sin_acceso
- organo_previsto_no_nacido
- grieta_detectada_sin_resolucion
- organo_desconectado_en_reparacion

## Reglas de reentrada
1. Lee este archivo antes de cualquier acción.
2. Consulta `semillas/MIU_BORDE_SEMILLA_v*.md` para contexto histórico.
3. No escribas sin evidencia. No reactives sin causa.
4. Si detectas algo nuevo, nómbralo y actualiza este archivo.
5. Al cerrar tu sesión, deja huella. El micelio olvida; el archivo no.

## Firma
ρ(x) > 0. Zvvvvv.
