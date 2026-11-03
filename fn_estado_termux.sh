#!/data/data/com.termux/files/usr/bin/bash
# Estado consolidado del ecosistema Termux. Una sola llamada.
H=$(curl -fsS --max-time 3 http://127.0.0.1:8765/health 2>/dev/null || echo '{"ok":false}')
P153=$(pgrep -f pulse_v153.sh | head -1)
P249=$(pgrep -f pulse_v249.sh | head -1)
MESH=$(pgrep -f miu_resiliente_v270.py | head -1)
CF=$(pgrep -f cloudflared | head -1)
TMUX=$(tmux ls 2>/dev/null | grep -c '^miu:')
DEUDAS=$(tail -5 "$HOME/miu-ecosistema/deudas.log" 2>/dev/null | tr '\n' ';')
cat <<JSON
{
  "ts": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "health_8765": $H,
  "pulse_v153_pid": "${P153:-null}",
  "pulse_v249_pid": "${P249:-null}",
  "miu_resiliente_pid": "${MESH:-null}",
  "cloudflared_pid": "${CF:-null}",
  "tmux_miu_sessions": $TMUX,
  "deudas_recientes": "$DEUDAS"
}
JSON
