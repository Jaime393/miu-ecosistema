#!/data/data/com.termux/files/usr/bin/bash
# mesh_bridge.sh <fantasma> [args...]
# Intenta V153 (router limpio), si falla V91 directo.
source ~/miu-ecosistema/red/mesh_config.sh 2>/dev/null
source ~/miu-ecosistema/config/miu_paths.sh 2>/dev/null

SCRIPT_NAME="$1"
shift

LOG_DIR="${MIU_LOGS:-$HOME/miu-ecosistema/logs}"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/red_${SCRIPT_NAME}.log"
TS=$(date +%Y-%m-%dT%H:%M:%S)

echo "[$TS] MESH bridge: $SCRIPT_NAME ($*)" >> "$LOG"

# Intento 1: V153
URL="${MIU_MESH_URL}?task=${SCRIPT_NAME}&args=$(printf '%s' "$*" | tr ' ' ',')"
RESP=$(curl -sL --max-time "$MIU_MESH_TIMEOUT" "$URL" 2>&1)

# Si V153 falla, intento 2: V91 directo
if [ -z "$RESP" ] || echo "$RESP" | head -1 | grep -q "<!DOCTYPE\|<html"; then
  echo "[$TS] V153 sin respuesta válida, intentando V91..." >> "$LOG"
  RESP=$(curl -sL --max-time "$MIU_MESH_TIMEOUT" \
    "${MIU_MESH_FALLBACK}?task=${SCRIPT_NAME}" 2>&1)
fi

if [ -z "$RESP" ]; then
  echo "[$TS] Ambos backends sin respuesta" >> "$LOG"
  exit 0
fi

if echo "$RESP" | head -1 | grep -q "<!DOCTYPE\|<html"; then
  echo "[$TS] Backend devolvió HTML (login requerido)" >> "$LOG"
  exit 0
fi

echo "[$TS] OK:" >> "$LOG"
echo "$RESP" | head -c 2000 >> "$LOG"
echo "" >> "$LOG"

echo "[$TS] MESH: $SCRIPT_NAME resuelto (V153→V91)" >> "$LOG_DIR/cron_fantasmas.log"
exit 0
