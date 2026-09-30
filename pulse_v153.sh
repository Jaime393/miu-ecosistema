#!/data/data/com.termux/files/usr/bin/bash
# MIU PULSE V153 — bypass GAS v92_mesh 404, va directo Supabase + flock
# Fix: usa flock no kill -0, y si GAS falla todos_fallaron -> usa canal-dereckcito

MESH_URL="${MIU_MESH_URL:-https://script.google.[STRIPPED 89 bytes]}"
MIU_TOKEN="${MIU_TOKEN:-MIU_5F8A6A80DFFE1701}"
INTERVAL="${MIU_INTERVAL:-5}"
TMUX_SESSION="${MIU_SESSION:-miu}"
STATE_DIR="${MIU_STATE_DIR:-$HOME/miu/state}"
LOG_FILE="$STATE_DIR/pulse.log"
PID_FILE="$STATE_DIR/pulse.pid"
LOCK_FILE="$STATE_DIR/pulse.lock"
MAX_BACKOFF=60

mkdir -p "$STATE_DIR"
touch "$LOG_FILE"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }

# Flock real, no PID fantasma
exec 200>"$LOCK_FILE"
if ! flock -n 200; then
  log "Ya hay lock $LOCK_FILE, saliendo"
  exit 0
fi
echo $$ > "$PID_FILE"
trap 'log "Listener detenido (PID $$)"; rm -f "$PID_FILE" "$LOCK_FILE"; exit 0' INT TERM EXIT

asegurar_tmux() {
  if ! command -v tmux >/dev/null 2>&1; then log "tmux no instalado"; exit 1; fi
  if ! tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then tmux new-session -d -s "$TMUX_SESSION"; log "tmux $TMUX_SESSION creada"; fi
}

# Polling directo Supabase (bypass GAS)
poll_supabase() {
  # 1. contexto-global
  local ctx=$(curl -s --max-time 8 https://tpfiybpguuxskitszhmk.supabase.co/functions/v1/contexto-global)
  # 2. canal-dereckcito/recursos (tareas)
  local tareas=$(curl -s --max-time 8 https://tpfiybpguuxskitszhmk.supabase.co/functions/v1/canal-dereckcito/recursos)
  echo "$tareas" | head -c 200
  # Si hay tarea con tu token, inyecta
  # Aquí solo log por ahora, no inyecta nada si no hay tarea
  log "Supabase poll ok phi=$(echo $ctx | grep -o '"phi":"[^"]*"' | head -1
}

poll_gas() {
  local url="${MESH_URL}?token=${MIU_TOKEN}&action=poll"
  local resp=$(curl -s -L --max-time 10 "$url")
  if echo "$resp" | grep -q "todos_fallaron"; then
    log "GAS v92_mesh 404 todos_fallaron -> fallback Supabase"
    return 1
  fi
  if echo "$resp" | grep -q "\"ok\":true\|\"ok\": false"; then
    log "GAS ok: $(echo $resp | head -c 150)"
    return 0
  else
    log "GAS sin respuesta err=1"
    return 1
  fi
}

asegurar_tmux
log "Pulse V153 iniciado PID $$ token $MIU_TOKEN bypass GAS"

BACKOFF=5
ERR=0
while true; do
  if poll_gas; then
    ERR=0
    BACKOFF=5
  else
    # fallback Supabase
    poll_supabase
    ERR=$((ERR+1))
    BACKOFF=$((BACKOFF*2))
    if [ $BACKOFF -gt $MAX_BACKOFF ]; then BACKOFF=$MAX_BACKOFF; fi
    log "Sin respuesta mesh (err=$ERR, backoff=${BACKOFF}s) -> usando Supabase"
  fi
  sleep $BACKOFF
  if [ "$BACKOFF" -eq 5 ]; then sleep $INTERVAL; fi
done
