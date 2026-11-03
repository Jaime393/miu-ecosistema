#!/data/data/com.termux/files/usr/bin/bash
# Sondea el mesh. Devuelve estado y registra deuda si falla.
MESH_URL="${MIU_MESH_URL:-https://script.google.com/macros/s/AKfycbxZR4V4q5s833ZT2VwBIf_8VmeVTmhX1iJlgbLBV_6zhUMu92K5cp5_dLo1XMf7GEs/exec}"
TOKEN="${MIU_TOKEN:-MIU_5F8A6A80DFFE1701}"
LOG="$HOME/miu-ecosistema/logs/mesh_probe.log"
RESP=$(curl -s -L --max-time 10 "${MESH_URL}?token=${TOKEN}&action=ping" 2>/dev/null)
if echo "$RESP" | grep -q '"ok"'; then
  echo "MESH_OK"
  echo "[$(date '+%F %T')] MESH_OK" >> "$LOG"
else
  echo "MESH_DEAD"
  echo "[$(date '+%F %T')] MESH_DEAD: ${RESP:0:200}" >> "$LOG"
  echo "[$(date '+%F %T')] deuda_mesh_404: GAS v92 responde 404, mesh no operativo" >> "$HOME/miu-ecosistema/deudas.log"
fi
