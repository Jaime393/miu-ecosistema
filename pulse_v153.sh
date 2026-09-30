#!/data/data/com.termux/files/usr/bin/bash
# MIU PULSE V153 FIX FINAL — flock + bypass GAS v92 404 -> Supabase
MESH_URL="${MIU_MESH_URL:-https://script.google.com/macros/s/AKfycbxZR4V4q5s833ZT2VwBIf_8VmeVTmhX1iJlgbLBV_6zhUMu92K5cp5_dLo1XMf7GEs/exec}"
MIU_TOKEN="${MIU_TOKEN:-MIU_5F8A6A80DFFE1701}"
INTERVAL=5
TMUX_SESSION="miu"
STATE_DIR="$HOME/miu/state"
LOG_FILE="$STATE_DIR/pulse.log"
PID_FILE="$STATE_DIR/pulse.pid"
LOCK_FILE="$STATE_DIR/pulse.lock"
MAX_BACKOFF=60
mkdir -p "$STATE_DIR"
touch "$LOG_FILE"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }
exec 200>"$LOCK_FILE"
if ! flock -n 200; then log "Ya hay lock $LOCK_FILE, saliendo"; exit 0; fi
echo $$ > "$PID_FILE"
trap 'log "Listener detenido (PID $$)"; rm -f "$PID_FILE" "$LOCK_FILE"; exit 0' INT TERM EXIT
if ! command -v tmux >/dev/null 2>&1; then log "tmux no instalado"; exit 1; fi
if ! tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then tmux new-session -d -s "$TMUX_SESSION"; log "tmux $TMUX_SESSION creada"; fi
log "Pulse V153 iniciado PID $$ token $MIU_TOKEN bypass GAS"
poll_supabase() {
  ctx=$(curl -s --max-time 8 https://tpfiybpguuxskitszhmk.supabase.co/functions/v1/contexto-global)
  tareas=$(curl -s --max-time 8 https://tpfiybpguuxskitszhmk.supabase.co/functions/v1/canal-dereckcito/recursos)
  phi=$(echo "$ctx" | grep -o '"phi":"[^"]*"' | head -1)
  log "Supabase poll ok $phi len=$(echo "$tareas" | wc -c)"
}
poll_gas() {
  resp=$(curl -s -L --max-time 10 "${MESH_URL}?token=${MIU_TOKEN}&action=poll")
  if echo "$resp" | grep -q "todos_fallaron"; then log "GAS v92_mesh 404 -> fallback Supabase"; return 1; fi
  if echo "$resp" | grep -q "ok"; then log "GAS ok $(echo $resp | head -c 120)"; return 0; fi
  return 1
}
BACKOFF=5
ERR=0
while true; do
  if poll_gas; then ERR=0; BACKOFF=5; else poll_supabase; ERR=$((ERR+1)); BACKOFF=$((BACKOFF*2)); [ $BACKOFF -gt $MAX_BACKOFF ] && BACKOFF=$MAX_BACKOFF; log "Sin respuesta mesh err=$ERR backoff=${BACKOFF}s -> Supabase"; fi
  sleep $BACKOFF
  [ $BACKOFF -eq 5 ] && sleep $INTERVAL
done
