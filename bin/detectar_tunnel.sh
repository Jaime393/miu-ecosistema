#!/data/data/com.termux/files/usr/bin/bash
set -u
STATE_DIR="$HOME/miu-ecosistema/.state"
TUNNEL_FILE="$STATE_DIR/tunnel_url.txt"
LOG_FILE="$STATE_DIR/detectar_tunnel.log"
mkdir -p "$STATE_DIR"

URL_VIVA=""

# Prioridad 1: log manual (el más fiable)
if [ -r "$HOME/cloudflared_live.log" ]; then
  URL_VIVA=$(grep -Eo 'https://[a-z0-9-]+\.trycloudflare\.com' "$HOME/cloudflared_live.log" 2>/dev/null | tail -1)
fi

# Prioridad 2: verificar que responde
if [ -n "$URL_VIVA" ]; then
  CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 6 "$URL_VIVA" 2>/dev/null)
  case "$CODE" in
    200|502|404) ;;
    *) URL_VIVA="" ;;
  esac
fi

# Prioridad 3: fallback a logs antiguos
if [ -z "$URL_VIVA" ]; then
  for CANDIDATA in $(grep -hEo 'https://[a-z0-9-]+\.trycloudflare\.com' \
      ~/cloudflared_live.log ~/cloudflared_v27.log ~/.state/cf_tunnel.log 2>/dev/null \
      | sort -u | tail -8); do
    CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 6 "$CANDIDATA" 2>/dev/null)
    if [ "$CODE" = "200" ] || [ "$CODE" = "502" ]; then
      URL_VIVA="$CANDIDATA"; break
    fi
  done
fi

if [ -n "$URL_VIVA" ]; then
  echo "$URL_VIVA" > "$TUNNEL_FILE"
  echo "[$(date -u +%FT%TZ)] URL: $URL_VIVA" >> "$LOG_FILE"
else
  echo "[$(date -u +%FT%TZ)] sin URL viva" >> "$LOG_FILE"
fi
