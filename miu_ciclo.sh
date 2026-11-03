#!/data/data/com.termux/files/usr/bin/bash
# ~/miu-ecosistema/miu_ciclo.sh — bucle de vida autónomo v1
# No es un parche. Es el metabolismo del nodo.
# Corre cada 15 min. Si algo falla, registra deuda y sigue.

BASE="$HOME/miu-ecosistema"
LOG="$BASE/logs/miu_ciclo.log"
DEUDAS="$BASE/deudas.log"
LOCK="$BASE/.miu_ciclo.lock"
TIMEOUT=120  # segundos por script

mkdir -p "$BASE/logs"
log() { echo "[$(date '+%F %T')] $*" >> "$LOG"; }
deuda() { echo "[$(date '+%F %T')] $*" >> "$DEUDAS"; }

# Evitar solapamiento: si hay un ciclo corriendo, salir
if [ -e "$LOCK" ] && kill -0 "$(cat "$LOCK" 2>/dev/null)" 2>/dev/null; then
  log "ciclo anterior aún vivo (pid $(cat "$LOCK")); salgo"
  exit 0
fi
echo $$ > "$LOCK"
trap 'rm -f "$LOCK"' EXIT

log "=== CICLO INICIO (pid $$) ==="

# 1. Verificar resiliente; si no responde, arrancarlo
if ! curl -fsS --max-time 2 http://127.0.0.1:8765/health >/dev/null 2>&1; then
  log "resiliente caído; arrancando"
  ( cd "$BASE" && nohup python3 miu_resiliente_v270.py >> logs/miu_resiliente.log 2>&1 & )
  sleep 3
  if curl -fsS --max-time 2 http://127.0.0.1:8765/health >/dev/null 2>&1; then
    log "resiliente arrancado OK"
  else
    deuda "resiliente_no_arranca"
  fi
else
  log "resiliente OK"
fi

# 2. Verificar túnel; si no está, arrancarlo
if ! pgrep -f 'cloudflared tunnel' >/dev/null 2>&1; then
  log "túnel caído; arrancando tunel_auto.sh"
  if [ -x "$HOME/tunel_auto.sh" ]; then
    ( nohup "$HOME/tunel_auto.sh" >/dev/null 2>&1 < /dev/null & )
    sleep 3
    pgrep -f 'cloudflared tunnel' >/dev/null 2>&1 && log "túnel arrancado OK" || deuda "tunel_no_arranca"
  else
    deuda "tunel_auto.sh_no_existe"
  fi
else
  log "túnel OK"
fi

# 3. Función: ejecutar un script con timeout y registrar resultado
run_script() {
  local script="$1"
  local name; name=$(basename "$script")
  if [ ! -f "$script" ]; then
    deuda "$name_no_existe"
    return
  fi
  local ext="${script##*.}"
  local cmd
  case "$ext" in
    py) cmd="python3" ;;
    sh) cmd="bash" ;;
    *)  deuda "$name_ext_desconocida"; return ;;
  esac
  log "ejecutando $name (timeout ${TIMEOUT}s)"
  if timeout "$TIMEOUT" "$cmd" "$script" >> "$BASE/logs/$name.log" 2>&1; then
    log "$name OK"
  else
    local code=$?
    if [ "$code" -eq 124 ]; then
      deuda "$name_timeout_${TIMEOUT}s"
    else
      deuda "$name_fallo_code_$code"
    fi
    log "$name FALLO (code $code)"
  fi
}

# 4. Ejecutar en orden los scripts que existen (sin asumir args)
for s in \
  "$BASE/pulse_v153.sh" \
  "$BASE/sensorium_v213.py" \
  "$BASE/cazador_recursos.py" \
  "$BASE/oraculo_bolsillo_v213.py" \
  "$BASE/nudo_eterno_router.py" \
  "$BASE/router_darwiniano_v11_3_FIXED.sh" \
  "$BASE/bootstrap_nodo_cero_v213.sh"
do
  run_script "$s"
done

# 5. Registrar cierre
log "=== CICLO FIN (pid $$) ==="
