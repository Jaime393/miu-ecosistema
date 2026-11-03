#!/data/data/com.termux/files/usr/bin/bash
# Watchdog separado: si la URL no responde 3 veces, mata cloudflared
URL_FILE="$HOME/miu-ecosistema/.state/tunnel_stable.txt"
LOG="$HOME/cloudflared_live.log"
FAILS=0

while true; do
  sleep 30
  [ ! -f "$URL_FILE" ] && continue
  URL=$(cat "$URL_FILE" | tr -d '[:space:]')
  [ -z "$URL" ] && continue
  CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 8 "$URL/health" 2>/dev/null)
  case "$CODE" in
    200|404|502) FAILS=0 ;;
    *)
      FAILS=$((FAILS+1))
      echo "$(date) - HC fallo ($CODE) $FAILS/3" >> "$LOG"
      if [ $FAILS -ge 3 ]; then
        echo "$(date) - URL MUERTA 3x → matando cloudflared para forzar reconexión" >> "$LOG"
        pkill -f 'cloudflared tunnel --no-autoupdate' 2>/dev/null
        FAILS=0
        sleep 5
      fi
      ;;
  esac
done
