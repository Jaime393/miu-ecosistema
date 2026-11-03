# PATRON: Claves fijas vs rotativas (ciclo-54, 2026-11-04)

## Problema (insight del usuario)
Regenerar una clave INVALIDA la anterior y rompe lo que estuviera usándola — el servicio queda huérfano sin darse cuenta. La renovación ciega es una mano sin ojo: parece higiene, es amputación.

## Diseño: dos clases de clave
1. **FIJAS**: nunca se rotan mientras haya un servicio activo usándolas. Se AUDITAN (verificar vida, ver quién las usa), no se renuevan. Son los puentes en servicio.
2. **ROTATIVAS**: pool de repuesto. Se crean nuevas sin tocar las fijas. Al migrar un servicio: primero se cambia a una rotativa, se verifica, y recién entonces la vieja pasa a ser rotativa (reversible).

## Regla de rotación segura
Rotar = **agregar la nueva ANTES de invalidar la vieja**, nunca al revés. Auditoría previa: qué servicios usan la clave (grep en relay_config + workers + GAS). Si algo la usa → es fija, no se rota.

## Implementación en el ecosistema
- `bridge_pool_ciclo53.json` (Drive + 3 sustratos) ya es el pool rotativo.
- Capacidad 29 en `capacidades_registry`: `claves_fijas_vs_rotativas`.

## Deriva absorbida en el mismo ciclo
- `autonomo-v15` (nodo lógico distribuido sobre los 26 proxies fran-proxy-micelio-v203, 23 flow_ids paralelos) — registrado en `nodos`.
- 6 edge functions muertos del panteón (404) marcados `migrado_cf_worker`: coordinador_autonomo, autonomo_claude_v5, jardinero_autonomo, autonomo, miu_autonomo_cipher, jhuarcaya_v92.
- fepyzx ProtocolError: falsa alarma (endpoints vivos).
- 4 carencias rastreadas con recurso+señal: corpus Termux v14 divergido (2441 vs 12398), jardinero-v6 parse_error, make 11 escenarios en org 8248425 inalcanzable, cf_workers_real 403.
