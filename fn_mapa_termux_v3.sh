#!/data/data/com.termux/files/usr/bin/bash
# ~/miu-ecosistema/fn_mapa_termux_v3.sh
# Mapa vivo de los cinco bolsillos. No parchea. Diagnostica.

BASE="$HOME/miu-ecosistema"
OUT="$BASE/logs/mapa_termux_v3_$(date '+%Y%m%d_%H%M').json"
mkdir -p "$BASE/logs"
json_escape() { printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'; }

PROCS=$(ps aux | grep -E 'miu|cloudflared|enjambre|pulse|sensorium|cazador|oraculo|router|nudo|artemis' | grep -v grep | awk '{print $2"|"$11"|"$12}' | paste -sd ',' -)
PUERTOS=$(ss -tlnp 2>/dev/null | awk 'NR>1 {print $4}' | paste -sd ',' -)
HEALTH=$(curl -fsS --max-time 2 http://127.0.0.1:8765/health 2>/dev/null || echo '{"ok":false}')
TUNEL=$(pgrep -f 'cloudflared tunnel' >/dev/null 2>&1 && echo true || echo false)
SYMLINKS_ROTOS=$(find "$BASE" "$HOME/miu" "$HOME/miu-relay" "$HOME/miu-teclado-v152" -maxdepth 2 -type l ! -exec test -e {} \; -print 2>/dev/null | paste -sd ',' -)
SD_MOUNT=$(mountpoint -q /storage/25A9-180D 2>/dev/null && echo true || echo false)
PULSOS=$(find "$HOME/miu" "$HOME/miu-relay" "$HOME/miu-teclado-v152" "$BASE" -maxdepth 1 -name 'pulse*.sh' -type f 2>/dev/null | paste -sd ',' -)
CRON=$(crontab -l 2>/dev/null | grep -v '^#' | paste -sd ';' -)
DEUDAS=$(tail -20 "$BASE/deudas.log" 2>/dev/null | paste -sd ';' -)
TS=$(date -u '+%Y-%m-%dT%H:%M:%SZ')

cat > "$OUT" <<EOF
{
  "ts": "$TS",
  "home": "$HOME",
  "base": "$BASE",
  "sd_montada": $SD_MOUNT,
  "procesos": "$(json_escape "$PROCS")",
  "puertos": "$(json_escape "$PUERTOS")",
  "health": $(echo "$HEALTH" | tr -d '\n'),
  "tunel_activo": $TUNEL,
  "symlinks_rotos": "$(json_escape "$SYMLINKS_ROTOS")",
  "pulsos": "$(json_escape "$PULSOS")",
  "cron": "$(json_escape "$CRON")",
  "deudas": "$(json_escape "$DEUDAS")"
}
EOF
echo "[mapa_v3] $OUT"
cat "$OUT"
