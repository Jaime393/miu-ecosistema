#!/data/data/com.termux/files/usr/bin/bash
# Busca scripts ausentes en todos los montajes y rutas comunes.
BUSCAR=("orquestador_integrado_v24.py" "miu_enjambre.py" "rotador_logs_v1.py" "digest_dedup.sh" "ensure_llama.sh")
RUTAS=("$HOME" "/storage/25A9-180D" "/storage/emulated/0" "$HOME/miu-ecosistema" "$HOME/miu" "$HOME/miu-relay")
OUT="$HOME/miu-ecosistema/logs/busqueda_recursos_$(date +%Y%m%d_%H%M).log"
echo "[buscar] $(date)" | tee "$OUT"
for f in "${BUSCAR[@]}"; do
  echo "--- $f ---" | tee -a "$OUT"
  for r in "${RUTAS[@]}"; do
    [ -d "$r" ] || continue
    find "$r" -name "$f" -type f 2>/dev/null | head -5 | tee -a "$OUT"
  done
done
echo "[buscar] log=$OUT"
