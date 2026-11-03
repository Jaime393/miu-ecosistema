#!/data/data/com.termux/files/usr/bin/bash
# ensure_llama.sh — Watchdog del motor local llama-server
BIN="$HOME/miu-ecosistema/bin/llama-server"
MODEL="/storage/25A9-180D/modelos/franbot.gguf"
PORT=8080
LOG="$HOME/miu-ecosistema/logs/llama_watch.log"
mkdir -p "$(dirname "$LOG")"

if ! curl -s --max-time 2 "http://127.0.0.1:$PORT/health" | grep -q "ok"; then
  pkill -f "llama-server.*$PORT" 2>/dev/null
  sleep 1
  nohup "$BIN" -m "$MODEL" --port "$PORT" -c 512 --n-threads 2 >> "$LOG" 2>&1 &
  echo "[$(date)] llama-server reiniciado con $MODEL" >> "$LOG"
fi
