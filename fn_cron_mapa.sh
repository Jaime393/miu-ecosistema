#!/data/data/com.termux/files/usr/bin/bash
# ~/miu-ecosistema/fn_cron_mapa.sh
# Mapea la crontab. Verifica que cada script referenciado exista.
# Salida: un mapa en JSON + lista de scripts ausentes en deudas.log.

BASE="$HOME/miu-ecosistema"
OUT="$BASE/logs/cron_mapa_$(date '+%Y%m%d_%H%M').json"
DEUDAS="$BASE/deudas.log"
mkdir -p "$BASE/logs"

CRON=$(crontab -l 2>/dev/null)

# Extraer rutas absolutas y relativas referenciadas en la crontab
REFS=$(echo "$CRON" | grep -oE '\$HOME/[A-Za-z0-9_./-]+|~/[A-Za-z0-9_./-]+|/data/data/[A-Za-z0-9_./-]+' | sort -u)

echo "{" > "$OUT"
echo "  \"ts\": \"$(date -u '+%Y-%m-%dT%H:%M:%SZ')\"," >> "$OUT"
echo "  \"cron_raw\": $(echo "$CRON" | jq -Rs .)," >> "$OUT"
echo "  \"scripts\": [" >> "$OUT"

FIRST=1
for ref in $REFS; do
  # Expandir $HOME y ~
  path="${ref/\$HOME/$HOME}"
  path="${path/#\~/$HOME}"
  # Ignorar redirecciones (log files)
  case "$path" in
    *.log|*.tgz) continue ;;
  esac
  if [ -e "$path" ]; then
    estado="ok"
  else
    estado="ausente"
    echo "[$(date '+%F %T')] cron_ref_ausente: $path" >> "$DEUDAS"
  fi
  if [ $FIRST -eq 0 ]; then echo "," >> "$OUT"; fi
  FIRST=0
  echo "    {\"path\": \"$path\", \"estado\": \"$estado\"}" >> "$OUT"
done

echo "  ]" >> "$OUT"
echo "}" >> "$OUT"
echo "[cron_mapa] $OUT"
cat "$OUT"
