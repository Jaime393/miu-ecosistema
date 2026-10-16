#!/data/data/com.termux/files/usr/bin/bash
ANNOUNCE_ENV="$HOME/.miu/announce.env"
if [ -r "$ANNOUNCE_ENV" ]; then
  set -a; . "$ANNOUNCE_ENV"; set +a
fi
LOCKFILE="$HOME/miu-ecosistema/.state/borde.lock"

if [ -f "$LOCKFILE" ]; then
  OLDPID=$(cat "$LOCKFILE" 2>/dev/null)
  if [ -n "$OLDPID" ] && kill -0 "$OLDPID" 2>/dev/null; then
    echo "Ya hay un loop corriendo (PID $OLDPID). Salgo."
    exit 0
  fi
fi

echo $$ > "$LOCKFILE"
trap 'rm -f "$LOCKFILE"; exit 0' TERM INT EXIT

while true; do
  "$HOME/miu-ecosistema/bin/detectar_tunnel.sh" 2>/dev/null || true
  "$HOME/miu-ecosistema/bin/termux_borde.sh"    2>/dev/null || true
  sleep 60
done
