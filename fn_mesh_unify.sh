#!/data/data/com.termux/files/usr/bin/bash
# Unifica la configuración del mesh. Crea mesh.env canónico.
# Mejorado 2026-10-23: detecta ok:true correctamente, no solo "ok"
set -u

ENV="$HOME/miu-ecosistema/mesh.env"

# URLs candidatas en orden de preferencia
# 1° V153→V91 (mesh router clásico, el que usa pulse)
# 2° v270 (aporte_miu, flujo nuevo)
URLS_CANDIDATAS=(
  "https://script.google.com/macros/s/AKfycbywWkuw8Dx_tuS6wIufgbmHi00lLgQ5TIFBQOp7U--6EDzlWSz693P_ulPuflVKorI/exec"
  "https://script.google.com/macros/s/AKfycbwG6NVWjm97PuZP5oyc4G9jaQBk08iJ2pxEvKoddnjP3gonTi1kj6r7UKzQoWzZ9kGM/exec"
  "https://script.google.com/macros/s/AKfycbwJpCii0OhK_hKD6KbwzTxUlYnvytk7Jt6i6fK472bF6UqQgBFFuMv4uxND1JzayoRT/exec"
  "https://script.google.com/macros/s/AKfycbzpDYBgbtVVz1wjTcuCOk8pBYkJb__tN9gmyKVmnO47SBlbLr2iqKOjSOXncangJUvh/exec"
)

TOKEN="${MIU_TOKEN:-MIU_5F8A6A80DFFE1701}"

# Función honesta: detecta ok:true (no solo "ok")
test_url() {
  local url="$1" action="${2:-ping}"
  local resp
  resp="$(curl -s -L --max-time 15 "${url}?token=${TOKEN}&action=${action}" 2>/dev/null)"
  # Acepta ok:true en JSON (con o sin espacios)
  echo "$resp" | grep -qE '"ok"\s*:\s*true' && return 0
  return 1
}

ELEGIDA=""
for U in "${URLS_CANDIDATAS[@]}"; do
  if test_url "$U" "ping"; then
    ELEGIDA="$U"
    echo "[fn_mesh_unify] ✅ URL funcional: ${U:0:60}..."
    break
  fi
done

if [ -z "$ELEGIDA" ]; then
  echo "[fn_mesh_unify] ❌ Ninguna URL respondió ok:true"
  echo "[fn_mesh_unify] No se modifica mesh.env"
  exit 1
fi

# Verificar acción poll también
POLL_OK=0
test_url "$ELEGIDA" "poll" && POLL_OK=1

# Backup antes de escribir
[ -f "$ENV" ] && cp "$ENV" "$ENV.bak_$(date +%Y%m%d_%H%M%S)"

cat > "$ENV" <<ENVEOF
# mesh.env — configuración canónica del mesh
# Regenerado por fn_mesh_unify.sh: $(date -u +%FT%TZ)
export MIU_MESH_URL="$ELEGIDA"
export MIU_TOKEN="$TOKEN"
export MIU_MESH_PING_OK=1
export MIU_MESH_POLL_OK=$POLL_OK
if [ "$POLL_OK" = "1" ]; then export MIU_MESH_ACTION="poll"; else export MIU_MESH_ACTION="ping"; fi
export MIU_APORTE_URL="https://script.google.com/macros/s/AKfycbwG6NVWjm97PuZP5oyc4G9jaQBk08iJ2pxEvKoddnjP3gonTi1kj6r7UKzQoWzZ9kGM/exec"
ENVEOF

echo "[fn_mesh_unify] ping_ok=1 poll_ok=$POLL_OK"
echo "[fn_mesh_unify] env=$ENV"
