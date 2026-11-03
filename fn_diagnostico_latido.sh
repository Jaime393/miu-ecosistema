#!/data/data/com.termux/files/usr/bin/bash
# ~/miu-ecosistema/fn_diagnostico_latido.sh
# Prueba cada script del ecosistema con timeout corto.
# Identifica cuál cuelga. No espera. No bloquea.

BASE="$HOME/miu-ecosistema"
LOGS="$BASE/logs"
TIMEOUT=15
OUT="$LOGS/diagnostico_latido_$(date '+%Y%m%d_%H%M').log"
mkdir -p "$LOGS"
: > "$OUT"

run_one() {
  local script="$1"
  local name; name=$(basename "$script")
  local ext="${script##*.}"
  local cmd
  case "$ext" in
    py) cmd="python3" ;;
    sh) cmd="bash" ;;
    *) return ;;
  esac
  local start; start=$(date +%s)
  if timeout "$TIMEOUT" "$cmd" "$script" >> "$LOGS/_test_$name.log" 2>&1; then
    local dur=$(( $(date +%s) - start ))
    echo "OK    ${dur}s  $name" | tee -a "$OUT"
  else
    local code=$?
    local dur=$(( $(date +%s) - start ))
    if [ "$code" -eq 124 ]; then
      echo "HANG  >${TIMEOUT}s $name" | tee -a "$OUT"
      echo "[$(date '+%F %T')] diagnostico_hang: $name excedio ${TIMEOUT}s" >> "$BASE/deudas.log"
    else
      echo "FAIL  ${dur}s  $name (code $code)" | tee -a "$OUT"
      echo "[$(date '+%F %T')] diagnostico_fail: $name code $code" >> "$BASE/deudas.log"
    fi
  fi
}

# Probar en paralelo para no esperar en serie
for s in \
  "$BASE/miu_resiliente_v270.py" \
  "$BASE/pulse_v153.sh" \
  "$BASE/sensorium_v213.py" \
  "$BASE/cazador_recursos.py" \
  "$BASE/oraculo_bolsillo_v213.py" \
  "$BASE/nudo_eterno_router.py" \
  "$BASE/router_darwiniano_v11_3_FIXED.sh"
do
  [ -f "$s" ] && run_one "$s" &
done
wait
echo "[diag] $OUT"
