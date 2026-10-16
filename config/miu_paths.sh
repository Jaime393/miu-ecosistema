#!/data/data/com.termux/files/usr/bin/bash
# miu_paths.sh — Inyector de rutas flexibles del micelio
# Uso:  source ~/miu-ecosistema/config/miu_paths.sh
# Luego: echo $MIU_ECOSISTEMA  (contiene la ruta real encontrada)

PATHS_JSON="${MIU_PATHS_JSON:-$HOME/miu-ecosistema/config/paths.json}"

if [ ! -f "$PATHS_JSON" ]; then
  echo "[miu_paths] ERROR: no encuentro $PATHS_JSON" >&2
  return 1 2>/dev/null || exit 1
fi

# Extraer nombres y rutas con python (evita depender de jq)
eval "$(python3 - "$PATHS_JSON" << 'PY'
import json, sys
with open(sys.argv[1]) as f:
    data = json.load(f)
for name, info in data.get("paths", {}).items():
    primary = info.get("primary", "")
    fallbacks = info.get("fallbacks", [])
    candidates = [primary] + fallbacks
    # Emitir array de candidatos para bash
    cand_str = " ".join(f'"{c}"' for c in candidates if c)
    print(f'_MIU_CANDIDATES_{name}=({cand_str})')
PY
)"

# Para cada variable, resolver al primer candidato existente
for name in $(python3 -c "
import json
with open('$PATHS_JSON') as f:
    data = json.load(f)
print(' '.join(data.get('paths', {}).keys()))
"); do
  eval "_cands=( \"\${_MIU_CANDIDATES_${name}[@]}\" )"
  _found=""
  for c in "${_cands[@]}"; do
    if [ -e "$c" ]; then
      _found="$c"
      break
    fi
  done
  if [ -n "$_found" ]; then
    export "$name=$_found"
  else
    export "$name="
    echo "[miu_paths] AVISO: $name no encontrado en ninguna ruta" >&2
  fi
done

unset _MIU_CANDIDATES_* _cands _found 2>/dev/null || true

# Exportar también el mapa entero para scripts que quieran JSON
export MIU_PATHS_JSON="$PATHS_JSON"
export MIU_PATHS_LOADED=1
