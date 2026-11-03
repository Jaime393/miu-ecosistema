#!/data/data/com.termux/files/usr/bin/bash
# ~/miu-ecosistema/fn_resolver_canonicos.sh
# Descubre duplicados por basename, elige el más reciente, escribe canonico.conf.
# No borra, no mueve, no recrea symlinks. Solo dice la verdad.

BASE="$HOME/miu-ecosistema"
OUT="$BASE/canonico.conf"
LOG="$BASE/logs/resolver_canonicos.log"
mkdir -p "$BASE/logs"
: > "$OUT"

log() { echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }

# Buscar todos los archivos con el mismo basename en los bolsillos conocidos
for name in pulse.sh pulse_v152.sh pulse_v153.sh pulse_v249.sh; do
  mapfile -t files < <(find "$HOME/miu" "$HOME/miu-relay" "$HOME/miu-teclado-v152" "$BASE" -maxdepth 1 -name "$name" -type f 2>/dev/null)
  [ ${#files[@]} -eq 0 ] && continue

  # Elegir el más reciente por mtime
  canon=$(ls -t "${files[@]}" 2>/dev/null | head -1)
  log "canonico $name -> $canon"

  # Hashes para saber si son idénticos
  for f in "${files[@]}"; do
    h=$(sha256sum "$f" 2>/dev/null | awk '{print $1}')
    log "  hash $h  $f"
  done

  # Escribir en canonico.conf
  echo "${name%.sh}=$canon" >> "$OUT"
done

log "escrito $OUT"
cat "$OUT"
