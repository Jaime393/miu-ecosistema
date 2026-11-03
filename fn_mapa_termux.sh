#!/data/data/com.termux/files/usr/bin/bash
# ~/miu-ecosistema/fn_mapa_termux.sh — v4
# Mapea $HOME + miu-ecosistema. Verifica SD con test -w (no mountpoint).
# Incluye cron, symlinks rotos, scripts del cron ausentes.

BASE="$HOME/miu-ecosistema"
LOGS="$BASE/logs"
OUT="$LOGS/mapa_termux_v4_$(date '+%Y%m%d_%H%M').json"
mkdir -p "$LOGS"

# Verificar SD con test -w en lugar de mountpoint (que no existe en Termux)
SD_TARGET="/storage/25A9-180D/MIU_termux/logs"
if [ -d "$SD_TARGET" ] && [ -w "$SD_TARGET" ]; then
  SD_MONTADA=true
else
  SD_MONTADA=false
fi

# Scripts del cron ausentes
CRON_MISSING=$(crontab -l 2>/dev/null | grep -oE '\$HOME/[A-Za-z0-9_./-]+' | sed "s|\$HOME|$HOME|" | sort -u | while read -r p; do [ ! -e "$p" ] && echo "$p"; done | paste -sd ',' -)

# Symlinks rotos
SYMLINKS_ROTOS=$(find "$BASE" -maxdepth 2 -type l ! -exec test -e {} \; -print 2>/dev/null | paste -sd ',' -)

# Health y túnel
HEALTH=$(curl -fsS --max-time 2 http://127.0.0.1:8765/health 2>/dev/null || echo '{"ok":false}')
TUNEL=$(pgrep -f 'cloudflared tunnel' >/dev/null 2>&1 && echo true || echo false)

cat > "$OUT" <<EOF
{
  "ts": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
  "home": "$HOME",
  "base": "$BASE",
  "sd_montada": $SD_MONTADA,
  "sd_path": "$SD_TARGET",
  "health": $(echo "$HEALTH" | tr -d '\n'),
  "tunel_activo": $TUNEL,
  "symlinks_rotos": "$(echo "$SYMLINKS_ROTOS" | sed 's/"/\\"/g')",
  "cron_scripts_ausentes": "$(echo "$CRON_MISSING" | sed 's/"/\\"/g')"
}
EOF
echo "[mapa_v4] $OUT"
cat "$OUT"
