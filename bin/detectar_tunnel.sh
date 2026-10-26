#!/data/data/com.termux/files/usr/bin/bash
set -u
ST="$HOME/miu-ecosistema/.state"
STABLE="$ST/tunnel_stable.txt"; TUN="$ST/tunnel_url.txt"; CAND="$ST/tunnel_candidate.txt"
LOG="$ST/detectar_tunnel.log"
mkdir -p "$ST"
log() { echo "[$(date -u +%FT%TZ)] $*" >> "$LOG"; }

URL=$(grep -Eo 'https://[a-z0-9-]+\.trycloudflare\.com' "$HOME/cloudflared_live.log" 2>/dev/null | grep -v 'api\.trycloudflare' | tail -1)

if [ -z "$URL" ]; then log "sin candidata"; exit 0; fi
echo "$URL" > "$CAND"
log "candidata: $URL"

# Excluir api.trycloudflare.com explícitamente
case "$URL" in
  *api.trycloudflare.com*|*cloudflare.com/tunnel*) log "URL del API, no promuevo"; exit 0 ;;
esac

CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "${URL}/health" 2>/dev/null)
case "$CODE" in
  200|404|502)
    CUR=""
    [ -r "$STABLE" ] && CUR=$(cat "$STABLE" | tr -d '[:space:]')
    if [ "$CUR" != "$URL" ]; then
      if [ -n "$CUR" ]; then
        OLD=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "${CUR}/health" 2>/dev/null)
        case "$OLD" in
          200|404|502) log "actual $CUR viva ($OLD), no cambio" ;;
          *) echo "$URL" > "$STABLE"; echo "$URL" > "$TUN"; log "PROMOVIDA (actual murió: $OLD)" ;;
        esac
      else
        echo "$URL" > "$STABLE"; echo "$URL" > "$TUN"; log "PROMOVIDA (primera)"
      fi
    fi ;;
  *) log "candidata NO responde (HTTP $CODE)" ;;
esac
