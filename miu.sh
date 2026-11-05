#!/data/data/com.termux/files/usr/bin/bash
# miu — verificación rápida + fix silencioso
# Silencioso si todo OK. Reporta solo lo que repara.

set +e

ISSUES=0
ACTIONS=""

# Helper para verificar + reportar
check_service() {
    local port=$1 ep=$2 name=$3 restart_cmd=$4
    local code
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 "http://127.0.0.1:${port}${ep}" 2>/dev/null)
    if [ "$code" != "200" ]; then
        ISSUES=$((ISSUES+1))
        ACTIONS="${ACTIONS}  ✗ ${name} (:${port}) caído → relanzando\n"
        eval "$restart_cmd" 2>/dev/null
        sleep 2
    fi
}

# 1. Wakelock (silencioso, sin reportar)
termux-wake-lock 2>/dev/null

# 2. Servicios locales
check_service 8771 "/health" "oráculo" \
    'pkill -9 -f "oraculo_ask.py"; sleep 1; cd ~ && nohup python3 ~/oraculo_ask.py --daemon >> /storage/25A9-180D/oraculo/oraculo_ask.log 2>&1 &'

check_service 8766 "/" "borde" \
    'pkill -9 -f "oraculo_borde_v2.py"; sleep 1; cd ~ && nohup python3 ~/oraculo_borde_v2.py --daemon >> ~/oraculo_borde.log 2>&1 &'

check_service 8765 "/health" "resiliente" \
    'pkill -9 -f "miu_resiliente_v270.py"; sleep 1; cd ~/miu-ecosistema && nohup python3 miu_resiliente_v270.py >> logs/miu_resiliente.log 2>&1 &'

check_service 8080 "/v1/models" "llama-server" \
    'pkill -9 -f "llama-server"; sleep 1; nohup $PREFIX/bin/llama-server -m /storage/25A9-180D/modelos/SmolLM2-360M-Instruct-Q4_K_M.gguf --alias smollm2-360m -c 1024 -t 2 --host 127.0.0.1 --port 8080 --jinja >> ~/miu/state/llama_server.log 2>&1 &'

# 3. Túnel
URL=$(cat ~/miu-ecosistema/.state/bore_url.txt 2>/dev/null)
if [ -n "$URL" ]; then
    CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 8 "$URL/health" 2>/dev/null)
    if [ "$CODE" != "200" ]; then
        ISSUES=$((ISSUES+1))
        ACTIONS="${ACTIONS}  ✗ Túnel muerto → rotando backends\n"
        ~/oraculo/tunnel_pool.sh >/dev/null 2>&1
    fi
fi

# 4. Crond
if ! pgrep -x crond >/dev/null 2>&1; then
    ISSUES=$((ISSUES+1))
    ACTIONS="${ACTIONS}  ✗ crond muerto → relanzando\n"
    crond 2>/dev/null
fi

# 5. Cola atascada (>5 queued)
if [ -f ~/oraculo/queue.db ]; then
    Q_OLD=$(sqlite3 ~/oraculo/queue.db "SELECT COUNT(*) FROM queue WHERE estado='queued' AND ts_creado < datetime('now', '-10 minutes')" 2>/dev/null || echo 0)
    if [ "$Q_OLD" -gt 0 ]; then
        ISSUES=$((ISSUES+1))
        ACTIONS="${ACTIONS}  ✗ Cola atascada (${Q_OLD} órdenes) → procesando\n"
        python3 ~/oraculo/queue_worker.py >/dev/null 2>&1
    fi
fi

# 6. Heartbeat stale (>10 min = crond congelado)
if [ -f ~/oraculo/heartbeat.log ]; then
    AGE=$(($(date +%s) - $(stat -c '%Y' ~/oraculo/heartbeat.log 2>/dev/null || echo $(date +%s))))
    if [ "$AGE" -gt 600 ]; then
        ISSUES=$((ISSUES+1))
        ACTIONS="${ACTIONS}  ⚠ Heartbeat stale ($((AGE/60))min) → crond congelado?\n"
        # Forzar un heartbeat manual
        ~/oraculo/heartbeat.sh >/dev/null 2>&1
    fi
fi

# ═══════════════════════════════════════════════════════════
# OUTPUT: silencioso si todo OK, breve si hubo issues
# ═══════════════════════════════════════════════════════════
if [ "$ISSUES" -eq 0 ]; then
    # Todo OK → silencio total (o un check mínimo)
    echo "✓"
else
    echo ""
    echo "MIU — $ISSUES problema(s) reparado(s):"
    echo -e "$ACTIONS"
    echo ""
    # Verificación final
    OK=0
    for p in 8771 8766 8765 8080; do
        case $p in
            8771) e="/health" ;; 8766) e="/" ;; 8765) e="/health" ;; 8080) e="/v1/models" ;;
        esac
        C=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 "http://127.0.0.1:$p$e" 2>/dev/null)
        [ "$C" = "200" ] && OK=$((OK+1))
    done
    echo "  Estado final: $OK/4 servicios OK"
    URL=$(cat ~/miu-ecosistema/.state/bore_url.txt 2>/dev/null)
    [ -n "$URL" ] && echo "  Túnel: $(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "$URL/health" 2>/dev/null)"
fi

exit 0
