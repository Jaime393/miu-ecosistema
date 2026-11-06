#!/data/data/com.termux/files/usr/bin/bash
# ensure_llama.sh — Watchdog del motor local llama-server
BIN="$PREFIX/bin/llama-server"
MODEL="/storage/25A9-180D/modelos/SmolLM2-360M-Instruct-Q4_K_M.gguf"
PORT=8080
LOG="$HOME/miu-ecosistema/logs/llama_watch.log"
mkdir -p "$(dirname "$LOG")"

if ! curl -s --max-time 2 "http://127.0.0.1:$PORT/health" | grep -q "ok"; then
  pkill -f "llama-server.*$PORT" 2>/dev/null
  sleep 1
  nohup "$BIN" -m "$MODEL" --port "$PORT" -c 2048 -t 4 --alias smollm2-360m --jinja >> "$LOG" 2>&1 &
  echo "[$(date)] llama-server reiniciado con $MODEL" >> "$LOG"
fi
