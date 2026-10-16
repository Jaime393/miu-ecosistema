#!/data/data/com.termux/files/usr/bin/bash
# cron_ejecuta.sh <script> [args...]
# 1. Busca local. 2. Si no existe, busca stub de red. 3. Si no, registra fantasma.
source ~/miu-ecosistema/config/miu_paths.sh 2>/dev/null

SCRIPT="$1"
shift

CANDIDATOS=(
  "$HOME/$SCRIPT"
  "$MIU_ECOSISTEMA/$SCRIPT"
  "$MIU_ECOSISTEMA/nodos/$SCRIPT"
  "$HOME/miu/$SCRIPT"
  "$HOME/miu_slim/$SCRIPT"
)

ENCONTRADO=""
for c in "${CANDIDATOS[@]}"; do
  if [ -f "$c" ]; then
    ENCONTRADO="$c"
    break
  fi
done

LOG_DIR="${MIU_LOGS:-$HOME/miu-ecosistema/logs}"
mkdir -p "$LOG_DIR"

# --- Caso 1: existe local ---
if [ -n "$ENCONTRADO" ]; then
  case "$SCRIPT" in
    *.py) python3 "$ENCONTRADO" "$@" >> "$LOG_DIR/$(basename $SCRIPT).log" 2>&1 ;;
    *.sh) bash "$ENCONTRADO" "$@" >> "$LOG_DIR/$(basename $SCRIPT).log" 2>&1 ;;
    *) "$ENCONTRADO" "$@" >> "$LOG_DIR/$(basename $SCRIPT).log" 2>&1 ;;
  esac
  exit $?
fi

# --- Caso 2: existe stub de red ---
STUB="$HOME/miu-ecosistema/red/stubs/$SCRIPT"
if [ -f "$STUB" ]; then
  bash "$STUB" "$SCRIPT" "$@" >> "$LOG_DIR/red_${SCRIPT}.log" 2>&1
  exit 0
fi

# --- Caso 3: fantasma puro ---
echo "[$(date)] FANTASMA: $SCRIPT no existe ni local ni como stub de red" >> "$LOG_DIR/cron_fantasmas.log"
exit 0
