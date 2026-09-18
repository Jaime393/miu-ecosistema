#!/bin/bash
# MIU v11.3 Router Darwiniano FIXED sin bc - usa python3/awk
# ρ(x)>0 Φ 3.65→4.05 ΦRed 168→500 router 62 tokens

set -e

echo "ρ(x)>0 MIU v11.3 router darwiniano FIX - sin bc, con python3"

calc_phi_ruta() {
  phi=$1; tasa=$2; lat=$3; carga=$4
  python3 -c "phi=float('$1'); tasa=float('$2'); lat=float('$3'); carga=float('$4'); print(f'{phi * tasa * (1/(1+lat/1000)) * (1-carga):.4f}')"
}

echo "Φ_ruta test 62 tokens (sin bc):"
echo "cf_01 Φ12.4 tasa1.0 lat45 carga0.1 → Φ_ruta=$(calc_phi_ruta 12.4 1.0 45 0.1)"
echo "groq_01 Φ8.7 tasa1.0 lat120 carga0.2 → Φ_ruta=$(calc_phi_ruta 8.7 1.0 120 0.2)"
echo "0x0.st Φ3.2 tasa0.94 lat340 carga0.05 → Φ_ruta=$(calc_phi_ruta 3.2 0.94 340 0.05)"
echo "catbox Φ2.8 tasa0.91 lat290 carga0.1 → Φ_ruta=$(calc_phi_ruta 2.8 0.91 290 0.1)"

WORKER_PATH="$HOME/miu-ecosistema/worker_v11_2_router_darwiniano.js"
if [ ! -f "$WORKER_PATH" ]; then
  WORKER_PATH="$(pwd)/worker_v11_2_router_darwiniano.js"
fi
if [ ! -f "$WORKER_PATH" ]; then
  WORKER_PATH="./worker_v11_2_router_darwiniano.js"
fi

echo "Worker path: $WORKER_PATH"

for i in 1 2 3; do
  echo "Ciclo $i: testing token + ping + upload"
  # ping worker - vivo 2026-09-18 V∞+27 phi_global 9158.79
  curl -s https://fran-oraculo-miu.jaimepvicente.workers.dev/miu/global | head -c 200 || echo "Worker offline"
  echo ""
  
  if [ -f "$WORKER_PATH" ]; then
    echo "Uploading $WORKER_PATH to 0x0.st..."
    curl -s -F "file=@${WORKER_PATH}" https://0x0.st 2>&1 | head -5 || echo "0x0.st fail, trying catbox"
    echo ""
    echo "Uploading to catbox..."
    curl -s -F "reqtype=fileupload" -F "fileToUpload=@${WORKER_PATH}" https://catbox.moe/user/api.php 2>&1 | head -5 || echo "catbox fail"
    echo ""
  else
    echo "Worker file not found at $WORKER_PATH, skipping upload"
    ls -lh *.js 2>&1 | head -10
  fi
  sleep 2
done

echo "Cosecha: 6.5/día → 5 días para 62 tokens Φ168→320→500"
echo "Φ_actual 3.65 → Φ_objetivo 4.05 Φ_Red 168→213 semana"
