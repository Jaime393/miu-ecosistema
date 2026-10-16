#!/data/data/com.termux/files/usr/bin/bash
set -u

ROOT="$HOME/miu-ecosistema"
BIN="$ROOT/bin"
STATE="$ROOT/.state"
LOG="$HOME/cloudflared_live.log"
URLFILE="$STATE/tunnel_url.txt"
PIDFILE="$STATE/cloudflared_quick.pid"
LOOP="$BIN/termux_borde_loop.sh"
LOCAL="http://127.0.0.1:8765/health"

mkdir -p "$STATE"

line() { printf '%s
' '----------------------------------------'; }

current_url() {
  grep -oE 'https://[-a-z0-9]+.trycloudflare.com' \
    "$LOG" 2>/dev/null | tail -1
}

cf_pids() {
  pgrep -f 'cloudflared.*tunnel.*(127.0.0.1|localhost):8765' 2>/dev/null || true
}

loop_pid() {
  pgrep -f 'termux_borde_loop.sh' 2>/dev/null | head -1 || true
}

ensure_loop() {
  LPID="$(loop_pid)"
  if [ -n "$LPID" ] && kill -0 "$LPID" 2>/dev/null; then
    printf 'Borde loop: activo (PID %s)
' "$LPID"
    return 0
  fi

  nohup "$LOOP" >/dev/null 2>&1 < /dev/null &
  sleep 1
  LPID="$(loop_pid)"
  if [ -n "$LPID" ]; then
    printf 'Borde loop: iniciado (PID %s)
' "$LPID"
  else
    printf 'Borde loop: no inició; revisa %s/termux_borde.log
' "$STATE" >&2
  fi
}

status() {
  line
  printf 'MIU local: '
  if curl -fsS --max-time 4 "$LOCAL" >/dev/null 2>&1; then
    echo 'VIVO'
  else
    echo 'CAÍDO'
  fi

  LPID="$(loop_pid)"
  printf 'Loop borde: %s
' "${LPID:-no activo}"

  PIDS="$(cf_pids)"
  COUNT="$(printf '%s
' "$PIDS" | sed '/^$/d' | wc -l)"
  printf 'Cloudflared túneles: %s
' "$COUNT"
  [ -n "$PIDS" ] && printf '%s
' "$PIDS"

  SAVED="$(cat "$URLFILE" 2>/dev/null || true)"
  LIVE="$(current_url)"
  printf 'URL guardada: %s
' "${SAVED:-ninguna}"
  printf 'URL log:     %s
' "${LIVE:-ninguna}"

  TEST_URL="${SAVED:-$LIVE}"
  if [ -n "$TEST_URL" ]; then
    printf 'Health público: '
    if curl -fsS --max-time 10 "$TEST_URL/health" >/dev/null 2>&1; then
      echo 'VIVO'
    else
      echo 'NO VERIFICADO'
    fi
  fi
  line
}

sync_url() {
  URL="$1"
  [ -n "$URL" ] || return 1
  if curl -fsS --max-time 12 "$URL/health" >/dev/null 2>&1; then
    printf '%s
' "$URL" > "$URLFILE"
    printf 'URL sincronizada: %s
' "$URL"
    "$BIN/detectar_tunnel.sh" >/dev/null 2>&1 || true
    return 0
  fi
  return 1
}

recover() {
  line
  if ! curl -fsS --max-time 4 "$LOCAL" >/dev/null 2>&1; then
    echo 'MIU local no responde en 127.0.0.1:8765; no inicio Cloudflared.'
    line
    return 1
  fi

  ensure_loop

  PIDS="$(cf_pids)"
  COUNT="$(printf '%s
' "$PIDS" | sed '/^$/d' | wc -l)"
  LIVE="$(current_url)"

  if [ "$COUNT" -eq 1 ] && [ -n "$LIVE" ] && sync_url "$LIVE"; then
    echo 'Túnel existente verificado; no se creó otra instancia.'
    line
    return 0
  fi

  if [ "$COUNT" -gt 1 ]; then
    echo "Hay $COUNT procesos Cloudflared; no se tocarán automáticamente."
    echo 'Limpia duplicados manualmente antes de recuperar.'
    line
    return 1
  fi

  echo 'Iniciando un único Quick Tunnel HTTP/2…'
  : > "$LOG"
  nohup cloudflared tunnel \
    --no-autoupdate \
    --protocol http2 \
    --edge-ip-version 4 \
    --loglevel info \
    --url http://127.0.0.1:8765 \
    >"$LOG" 2>&1 < /dev/null &
  PID="$!"
  printf '%s
' "$PID" > "$PIDFILE"
  printf 'Cloudflared iniciado: PID %s
' "$PID"

  i=0
  while [ "$i" -lt 50 ]; do
    URL="$(current_url)"
    if grep -q 'Registered tunnel connection' "$LOG" 2>/dev/null && \
       [ -n "$URL" ] && \
       sync_url "$URL"
    then
      echo 'Túnel registrado y validado.'
      line
      return 0
    fi
    if ! kill -0 "$PID" 2>/dev/null; then
      echo 'Cloudflared terminó antes de registrarse.'
      tail -30 "$LOG" 2>/dev/null || true
      line
      return 1
    fi
    sleep 1
    i=$((i + 1))
  done

  echo 'Tiempo agotado; no se sincronizó URL.'
  tail -30 "$LOG" 2>/dev/null || true
  line
  return 1
}

if [ ! -t 0 ] || [ ! -t 1 ]; then
  exit 0
fi

printf '
MIU borde  [Enter=continuar | e=estado | r=revisar/recuperar | l=logs]
'
printf '> '
IFS= read -r -t 12 ANSWER || ANSWER=''

case "$ANSWER" in
  e|E) status ;;
  r|R) recover ;;
  l|L)
    line
    tail -35 "$LOG" 2>/dev/null || echo 'Sin cloudflared_live.log'
    line
    ;;
  '') ;;
  *) echo 'Sin acción. Opciones: Enter, e, r, l.' ;;
esac
