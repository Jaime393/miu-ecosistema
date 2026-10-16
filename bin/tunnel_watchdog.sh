#!/data/data/com.termux/files/usr/bin/sh
set -u

HOME_DIR="${HOME:?}"
ROOT="$HOME_DIR/miu-ecosistema"
STATE="$ROOT/.state"
LOG="$HOME_DIR/cloudflared_watchdog.log"
PIDFILE="$STATE/cloudflared_watchdog_tunnel.pid"
URLFILE="$STATE/tunnel_url.txt"
WLOG="$STATE/tunnel_watchdog.log"
ORIGIN="http://127.0.0.1:8765"
POLL_SECS=15
STARTUP_SECS=50

mkdir -p "$STATE"

ts() { date '+%Y-%m-%dT%H:%M:%S%z'; }
note() { printf '[%s] %s
' "$(ts)" "$*" >> "$WLOG"; }

origin_ok() {
  curl -fsS --max-time 8 "$ORIGIN/health" >/dev/null 2>&1
}

pid_alive() {
  [ -s "$PIDFILE" ] || return 1
  PID="$(cat "$PIDFILE" 2>/dev/null || true)"
  [ -n "$PID" ] || return 1
  kill -0 "$PID" 2>/dev/null || return 1
  tr '' ' ' < "/proc/$PID/cmdline" 2>/dev/null | grep -q 'cloudflared tunnel'
}

url_from_log() {
  grep -oE 'https://[-a-z0-9]+.trycloudflare.com' \
    "$LOG" 2>/dev/null | tail -1
}

is_registered() {
  grep -q 'Registered tunnel connection' "$LOG" 2>/dev/null
}

public_ok() {
  URL="$1"
  curl -fsS --max-time 15 "$URL/health" >/dev/null 2>&1
}

stop_owned() {
  if [ -s "$PIDFILE" ]; then
    OLD="$(cat "$PIDFILE" 2>/dev/null || true)"
    if [ -n "$OLD" ] && kill -0 "$OLD" 2>/dev/null; then
      tr '' ' ' < "/proc/$OLD/cmdline" 2>/dev/null | grep -q 'cloudflared tunnel' && \
        kill -TERM "$OLD" 2>/dev/null || true
      sleep 2
    fi
  fi
  rm -f "$PIDFILE"
}

start_tunnel() {
  stop_owned
  : > "$LOG"
  nohup cloudflared tunnel \
    --no-autoupdate \
    --protocol http2 \
    --edge-ip-version 4 \
    --loglevel info \
    --url "$ORIGIN" \
    >> "$LOG" 2>&1 < /dev/null &
  PID="$!"
  printf '%s
' "$PID" > "$PIDFILE"
  note "cloudflared_started pid=$PID"
}

sync_if_ready() {
  URL="$(url_from_log)"
  if [ -n "$URL" ] && is_registered && public_ok "$URL"; then
    OLD="$(cat "$URLFILE" 2>/dev/null || true)"
    if [ "$URL" != "$OLD" ]; then
      printf '%s
' "$URL" > "$URLFILE"
      note "url_synced url=$URL"
    fi
    return 0
  fi
  return 1
}

wait_for_ready() {
  elapsed=0
  while [ "$elapsed" -lt "$STARTUP_SECS" ]; do
    if ! pid_alive; then
      note "tunnel_exited_during_startup"
      return 1
    fi
    if sync_if_ready; then
      note "tunnel_ready"
      return 0
    fi
    sleep 2
    elapsed=$((elapsed + 2))
  done
  note "tunnel_startup_timeout"
  return 1
}

note "watchdog_started"

while :; do
  if ! origin_ok; then
    note "origin_unhealthy action=wait"
    sleep "$POLL_SECS"
    continue
  fi

  if ! pid_alive; then
    note "tunnel_not_running action=start"
    start_tunnel
    if ! wait_for_ready; then
      rm -f "$URLFILE"
      stop_owned
      sleep "$POLL_SECS"
      continue
    fi
  fi

  if sync_if_ready; then
    sleep "$POLL_SECS"
    continue
  fi

  note "tunnel_not_ready action=wait"
  sleep "$POLL_SECS"
done
