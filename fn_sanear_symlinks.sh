#!/data/data/com.termux/files/usr/bin/bash
# ~/miu-ecosistema/fn_sanear_symlinks.sh
# Detecta symlinks rotos. Si apuntan a un pulse_v152 ausente,
# los repunta al canónico vigente (pulse_v249.sh o pulse_v153.sh).
# NO borra. NO adivina. Verifica antes de tocar.

BASE="$HOME/miu-ecosistema"
CONF="$BASE/canonico.conf"
DEUDAS="$BASE/deudas.log"

# Elegir canónico: preferir el más reciente por mtime
CANON=""
for cand in "$HOME/miu/pulse_v249.sh" "$BASE/pulse_v153.sh" "$HOME/miu/pulse.sh"; do
  if [ -f "$cand" ]; then
    CANON="$cand"
    break
  fi
done

if [ -z "$CANON" ]; then
  echo "[sanear] no hay pulso canónico; abortando" | tee -a "$DEUDAS"
  exit 1
fi
echo "[sanear] canónico elegido: $CANON"

find "$BASE" -maxdepth 3 -type l | while read -r link; do
  target=$(readlink -f "$link" 2>/dev/null)
  if [ ! -e "$target" ]; then
    name=$(basename "$link")
    case "$name" in
      pulse_v152.sh)
        # Repuntar al canónico (sin borrar el link, reescribiendo el target)
        ln -sf "$CANON" "$link"
        echo "[sanear] repuntado: $link -> $CANON" | tee -a "$DEUDAS"
        ;;
      *)
        echo "[sanear] roto_no_manejado: $link -> $target" | tee -a "$DEUDAS"
        ;;
    esac
  fi
done
