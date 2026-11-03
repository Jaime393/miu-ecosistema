#!/data/data/com.termux/files/usr/bin/bash
# Ejecuta el pulso canónico con timeout duro. Nunca cuelga.
PULSE="${1:-$HOME/miu/pulse_v249.sh}"
LOG="$HOME/miu-ecosistema/logs/pulse_seguro_$(date +%Y%m%d_%H%M).log"
timeout -k 5 30 bash "$PULSE" >"$LOG" 2>&1
rc=$?
if [ $rc -eq 124 ]; then
  echo "[$(date '+%F %T')] pulse_hang: $PULSE" >> "$HOME/miu-ecosistema/deudas.log"
fi
echo "rc=$rc log=$LOG"
