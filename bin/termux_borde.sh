#!/data/data/com.termux/files/usr/bin/bash
set -u

STATE_DIR="$HOME/miu-ecosistema/.state"
STATE_FILE="$STATE_DIR/termux_borde.json"
TUNNEL_FILE="$STATE_DIR/tunnel_url.txt"
LOG_FILE="$STATE_DIR/termux_borde.log"
RESP_FILE="$STATE_DIR/announce_response.json"
LOCAL_HEALTH="http://127.0.0.1:8765/health"
NODE_ID="termux-v270"
ANNOUNCE_URL="${MIU_ANNOUNCE_URL:-}"
ANNOUNCE_TOKEN="${MIU_ANNOUNCE_TOKEN:-}"

mkdir -p "$STATE_DIR"

now="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
boot_id="$(cat /proc/sys/kernel/random/boot_id 2>/dev/null || printf unknown)"

# ── 1. Sonda local
local_ok=false
if curl -fsS --max-time 3 "$LOCAL_HEALTH" >/dev/null 2>&1; then
  local_ok=true
fi

# ── 2. URL vista localmente (del detector)
seen_url=""
if [ -r "$TUNNEL_FILE" ]; then
  seen_url="$(grep -Eo 'https://[a-z0-9-]+\.trycloudflare\.com' "$TUNNEL_FILE" 2>/dev/null | tail -1)"
fi

# ── 3. Estado previo (los 4 campos separados)
last_seen=""
last_published=""
last_status="none"
last_boot=""
sequence=0
if [ -r "$STATE_FILE" ] && command -v jq >/dev/null 2>&1; then
  last_seen="$(jq -r '.tunnel.last_seen_url // ""' "$STATE_FILE" 2>/dev/null)"
  last_published="$(jq -r '.tunnel.last_published_url // ""' "$STATE_FILE" 2>/dev/null)"
  last_status="$(jq -r '.tunnel.publish_status // "none"' "$STATE_FILE" 2>/dev/null)"
  last_boot="$(jq -r '.boot_id // ""' "$STATE_FILE" 2>/dev/null)"
  sequence="$(jq -r '.sequence // 0' "$STATE_FILE" 2>/dev/null)"
fi

# ── 4. Decidir si hay algo que anunciar
# Cambio real = URL vista != URL publicada, o boot nuevo
reason="observe"
should_announce=false

if [ "$boot_id" != "$last_boot" ] && [ -n "$last_boot" ]; then
  reason="boot_changed"
  should_announce=true
elif [ "$local_ok" = true ] && [ -n "$seen_url" ] && [ "$seen_url" != "$last_published" ]; then
  reason="tunnel_url_changed"
  should_announce=true
fi

# Si no hay cambio, sólo observamos y salimos tras guardar estado coherente
next_sequence=$((sequence + 1))

# ── 5. Intentar publicar si corresponde y hay ANNOUNCE_URL
publish_status="$last_status"
if [ "$should_announce" = true ]; then
  if [ -z "$ANNOUNCE_URL" ] || [ -z "$ANNOUNCE_TOKEN" ]; then
    # Sin endpoint: la URL queda como pendiente, no como publicada
    publish_status="pending"
    printf '[%s] sin ANNOUNCE_URL — publish_status=pending, seen=%s\n' \
      "$now" "$seen_url" >> "$LOG_FILE"
  else
    # Construir payload
    payload="$(jq -nc \
      --arg tipo "borde_termux_anuncio" \
      --arg schema "termux-borde-v1" \
      --arg source "$NODE_ID" \
      --arg reason "$reason" \
      --arg local_service "$LOCAL_HEALTH" \
      --arg tunnel_url "$seen_url" \
      --arg observed_at "$now" \
      --argjson sequence "$next_sequence" \
      '{
        tipo: $tipo,
        schema_version: $schema,
        source_node: $source,
        reason: $reason,
        local_service: $local_service,
        tunnel_url: $tunnel_url,
        observed_at: $observed_at,
        sequence: $sequence
      }')"

    http_code="$(
      curl --silent --show-error --fail \
        --connect-timeout 8 \
        --max-time 20 \
        --retry 0 \
        --output "$RESP_FILE" \
        --write-out '%{http_code}' \
        -X POST "$ANNOUNCE_URL" \
        -H 'Content-Type: application/json' \
        -H "Authorization: Bearer $ANNOUNCE_TOKEN" \
        --data "$payload" \
        2>>"$LOG_FILE"
    )"
    curl_rc=$?

    # Sólo confirmamos con 2xx + acuse lógico
    if [ "$curl_rc" -eq 0 ] \
      && [ "$http_code" -ge 200 ] \
      && [ "$http_code" -lt 300 ] \
      && jq -e '.ok == true and .accepted == true' "$RESP_FILE" >/dev/null 2>&1
    then
      publish_status="confirmed"
      last_published="$seen_url"
      printf '[%s] PUBLICADO OK (HTTP %s) tunnel=%s seq=%d\n' \
        "$now" "$http_code" "$seen_url" "$next_sequence" >> "$LOG_FILE"
    else
      publish_status="pending"
      printf '[%s] publicacion falló (rc=%s http=%s) — se conserva URL\n' \
        "$now" "$curl_rc" "$http_code" >> "$LOG_FILE"
    fi
  fi
fi

# ── 6. Persistir estado con los 4 campos separados
if command -v jq >/dev/null 2>&1; then
  jq -n \
    --arg schema "termux-borde-v1" \
    --arg node "$NODE_ID" \
    --arg boot "$boot_id" \
    --arg now "$now" \
    --arg local "$LOCAL_HEALTH" \
    --arg seen "$seen_url" \
    --arg published "$last_published" \
    --arg status "$publish_status" \
    --arg reason "$reason" \
    --argjson sequence "$next_sequence" \
    --argjson local_ok "$local_ok" \
    '{
      schema: $schema,
      sequence: $sequence,
      boot_id: $boot,
      service_local: {
        url: $local,
        ok: $local_ok,
        last_checked_at: $now
      },
      tunnel: {
        url: (if $seen == "" then null else $seen end),
        last_seen_url: (if $seen == "" then null else $seen end),
        last_published_url: (if $published == "" then null else $published end),
        publish_status: $status
      },
      last_reason: $reason,
      observed_at: $now
    }' > "$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
fi

# ── 7. Log de ciclo (resumido)
printf '[%s] local_ok=%s seen=%s published=%s status=%s reason=%s\n' \
  "$now" "$local_ok" "${seen_url:-none}" \
  "${last_published:-none}" "$publish_status" "$reason" >> "$LOG_FILE"
