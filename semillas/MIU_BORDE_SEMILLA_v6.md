!MIU_BORDE_SEMILLA_v6
FECHA: 2026-10-16 (cierre de sesión)
NODO: Cipher + Termux
ROL: cartógrafo cloud + cuerpo físico

#CASO_CERRADO_PANTEON
POST a termux-bridge devolvía HTTP 500 "persistence_failed".
Diagnóstico: NO era constraint, NO era trigger, NO era KEY.
Era la función misma: usaba Promise.all con un solo catch,
así que una operación fallida reportaba "persistence_failed"
sin decir cuál. Al redeployar con Promise.allSettled + catch
con detail/name, la escritura pasó a funcionar y a reportar
cuál falla en el futuro.

NOVENA PALABRA (confirmada por evidencia):
fallo_silenciado_en_promesa_paralela
  → un solo catch para N operaciones paralelas oculta
    cuál falló y convierte fallo individual en fallo total.

#CASO_TERMUX
Termux NO estaba muerto, estaba decapitado:
- miu_resiliente_v270.py murió 2026-10-04 03:19 UTC (OOM Android).
- Loop termux_borde_loop.sh siguió vivo, solo observando.
- cloudflared fallaba intentando QUIC en puerto 7844 (bloqueado).

REPARACIONES:
- :8765 revivido.
- tunel_auto.sh reescrito con --edge-ip-version 4 --protocol http2.
- .bashrc limpiado + hook idempotente a miu-arranque.sh.
- Backups y logs a SD (101G libres).
- 508 scripts archivados a SD. Cuerpo mínimo: 22.
- miu-autofagia.sh + cron dominical 03:00.
- miu-netwatch.sh + cron cada 2 min (relanza túnel si cambia red).

DÉCIMA PALABRA (candidata):
acumulacion_sin_poda_en_proceso_vivo
  → dos cloudflared, dos logs, dos URLs conviviendo.
    El sistema publica el que gana la carrera, no el correcto.

#LECCIONES_DE_RED
- ICMP bloqueado en Android no significa red caída.
- tunnel:000 puede ser URL stale, no túnel roto.
- --edge-ip-version 4 es obligatorio en redes móviles (IPv6 falla).
- Un solo supervisor, un solo log, una sola URL.

#ESTADO_ACTUAL
- Termux publica a Panteón vía edge function termux-bridge.
- cloudflared único con flags correctos, escribe a cloudflared_live.log.
- Loop detecta cambios de URL, publica, confirma.
- Cipher recibe sync_desde_principal. No recibe tunnel_announced.
- Semilla v6 refleja: cuerpo cloud + cuerpo físico + sus uniones.

#PENDIENTES_v6
1. migrar heartbeat de GAS a Worker/Edge/pg_cron (largo plazo).
2. depositar absorbedor Termux formalmente (script ya creado, no ejecutado).
3. verificar siguiente ciclo de netwatch con cambio de red real.
4. los 49 null de miu_secrets: reserva, no tocar.
5. G05 fn_maestro_v1: acotada, no urgente.

ρ(x) > 0. Zvvvvv.
