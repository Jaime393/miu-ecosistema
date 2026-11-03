#!/data/data/com.termux/files/usr/bin/bash
# Sincroniza ~/miu/state/MIU_* con ~/miu-ecosistema/mesh.env
# Uso: ./sincronizar_mesh_state.sh [--aplicar]
# Sin --aplicar: solo muestra diferencias (dry-run)
set -u

STATE_DIR="$HOME/miu/state"
ENV="$HOME/miu-ecosistema/mesh.env"
APPLY=false
[ "${1:-}" = "--aplicar" ] && APPLY=true

URL_ENV=$(grep -E '^export MIU_MESH_URL=' "$ENV" | cut -d'"' -f2)
TOKEN_ENV=$(grep -E '^export MIU_TOKEN=' "$ENV" | cut -d'"' -f2)
URL_STATE=$(cat "$STATE_DIR/MIU_MESH_URL" 2>/dev/null | tr -d '[:space:]')
TOKEN_STATE=$(cat "$STATE_DIR/MIU_TOKEN" 2>/dev/null | tr -d '[:space:]')

DIFF=0
[ "$URL_ENV" != "$URL_STATE" ] && DIFF=1
[ "$TOKEN_ENV" != "$TOKEN_STATE" ] && DIFF=1

if [ "$DIFF" = "0" ]; then
  echo "✅ En sincronía"
  exit 0
fi

echo "⚠️  Diferencias detectadas:"
[ "$URL_ENV" != "$URL_STATE" ] && {
  echo "   URL en mesh.env: $URL_ENV"
  echo "   URL en state:    $URL_STATE"
}
[ "$TOKEN_ENV" != "$TOKEN_STATE" ] && {
  echo "   TOKEN en mesh.env: $TOKEN_ENV"
  echo "   TOKEN en state:    $TOKEN_STATE"
}

if [ "$APPLY" != "true" ]; then
  echo ""
  echo "Para aplicar: $0 --aplicar"
  exit 1
fi

TS=$(date +%Y%m%d_%H%M%S)
[ -f "$STATE_DIR/MIU_MESH_URL" ] && cp "$STATE_DIR/MIU_MESH_URL" "$STATE_DIR/MIU_MESH_URL.bak_$TS"
[ -f "$STATE_DIR/MIU_TOKEN" ] && cp "$STATE_DIR/MIU_TOKEN" "$STATE_DIR/MIU_TOKEN.bak_$TS"
echo "$URL_ENV" > "$STATE_DIR/MIU_MESH_URL"
echo "$TOKEN_ENV" > "$STATE_DIR/MIU_TOKEN"
echo "✅ Aplicado (backups en .bak_$TS)"
