#!/data/data/com.termux/files/usr/bin/bash
# ~/miu-ecosistema/fn_latido_desde_canonico.sh
# Ejecuta el pulso canónico + autofagia + netwatch si existen.
# No depende de nombres fijos: lee canonico.conf.

BASE="$HOME/miu-ecosistema"
CONF="$BASE/canonico.conf"
LOG="$BASE/logs/latido_canonico.log"
DEUDAS="$BASE/deudas.log"
mkdir -p "$BASE/logs"

log() { echo "[$(date '+%F %T')] $*" >> "$LOG"; }
deuda() { echo "[$(date '+%F %T')] $*" >> "$DEUDAS"; }

# Cargar canonico.conf si existe
if [ -f "$CONF" ]; then
  source "$CONF" 2>/dev/null
fi

run() {
  local script="$1"; local name; name=$(basename "$script")
  [ -f "$script" ] || { deuda "$name_no_existe"; return; }
  local cmd="bash"; [ "${script##*.}" = "py" ] && cmd="python3"
  log "ejecutando $name"
  if timeout 120 "$cmd" "$script" >> "$BASE/logs/$name.log" 2>&1; then
    log "$name OK"
  else
    local code=$?
    [ "$code" -eq 124 ] && deuda "$name_timeout" || deuda "$name_fallo_$code"
    log "$name FALLO ($code)"
  fi
}

# Pulso canónico (si el resolver lo encontró)
if [ -n "$pulse" ] && [ -f "$pulse" ]; then
  run "$pulse"
else
  deuda "pulse_canonico_no_definido"
fi

# Otros latidos del HOME
for s in "$HOME/miu-autofagia.sh" "$HOME/miu-netwatch.sh" "$HOME/tunel_auto.sh"; do
  [ -f "$s" ] && run "$s"
done

log "latido completo"
