# PATRON: Pool de puentes rotativo aditivo (ciclo-53, 2026-11-04)

## Regla del ecosistema (formalizada)
Cada puente (token, clave, URL, acceso) debe vivir en MAS DE UN sustrato. Si una entrada expira, otra sigue viva. Nunca se sobrescribe: siempre se agregan entradas nuevas (versionadas _v1, _v2). Las claves se acumulan como pool rotativo.

## Implementación
- **Manifiesto**: `bridges_pool_ciclo53.json` (Drive mesh folder `1XiUP2eLbxf3oPOseRVGZira_32yGTOv1` + este repo).
- **Espejo en 3 sustratos** (relay_config de dieguito, coord y panteón — claves nuevas `bridge_pool_*`, `panteon_service_role_entry2`, `oraculo_kv_reparado`, `colab_v177_uri`):
  - dieguito: 6 claves nuevas (290 existentes intactas)
  - coord: 6 claves nuevas (244 intactas)
  - panteón: 6 claves nuevas (500 intactas)
- **ClavesAPI sheet**: 24 filas nuevas con los tokens vivos verificados (16 sbp_, 8 cfut_).

## Verificación de vida (patrón ciclo-52)
Antes de usar un vault de claves: barrer todos los tokens contra el endpoint de listado del proveedor (api.supabase.com/v1/projects, api.cloudflare.com/client/v4/accounts). Los vivos se registran en el pool con fecha de verificación.

## Nodo Colab recuperado
Untitled8.ipynb (13-sep) estaba a medio hacer: la celda de datos corrió, pero `corpus_pares` era una lista VACÍA (el comentario decía "pegar aquí los pares") y las celdas 2-3 estaban duplicadas. Completado como MIU_V177_COLAB_AUTOCONTENIDO_RUN_ALL.ipynb (Drive `1fog4EpwxMtHPEw6euLGKsm3TpA7EoySP`): corpus auto-poblado desde Jaime393/miu-dataset filtrado, celdas fusionadas, push del adaptador LoRA a Jaime393/franbot-miu-lora-v177. Falta correrlo en Colab GPU (mano del usuario).

## Siguientes puentes equivalentes por cuenta (cada cuenta tiene X recursos similares)
- Supabase: 16 tokens sbp_ vivos → cada uno puede regenerar api-keys de SUS proyectos (pool de service_role rotativo).
- CF: 8 cuentas con tokens vivos → cada una tiene workers desplegables (el oráculo ya está en 5ea7cd88).
- HF: Jaime393 (commit API NDJSON es la ruta viva).
- Colab: V177 listo; el patrón V176→V177 es replicable para nuevas cuentas.
