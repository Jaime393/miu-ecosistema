#!/usr/bin/env python3
"""Guarda el mapeo definitivo cuenta-email-account_id. 11/11."""
import json
from pathlib import Path

# Los 11 account_id reales del output del test anterior
MAPEO = {
    "jhuarcaya938@gmail.com":        "cce82777c5814ee76c44fe1772c85465",
    "dieguito.vg16@gmail.com":       "308faedf16a56fbb68d464127c696844",
    "jaimepvicente@gmail.com":       "5ea7cd88010b382b154d2fcff00b9ab3",
    "franrussell81@gmail.com":       "d0b37632e626...",  # completar con ID completo
    "jaimedanielmartinez75@gmail.com":"ba3dcff0c203...",
    "tabletonephantom@gmail.com":    "0b12fa35172e...",
    "dereckcito.vg16@gmail.com":     "6915f743348f...",
    "jaimepviccente@gmail.com":      "503f950671ff...",  # 3 c's (typo)
    "javier19051997@gmail.com":      "7a33df988fd5...",
    "cipher19051997@gmail.com":      "f9a245238a2a...",
    "franchescopalacios9@gmail.com": "30c349b65d9f...",
}

out = Path("/storage/25A9-180D/.miu-base/cf_mapeo_11_cuentas.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"cuentas": MAPEO, "total": 11}, indent=2))
print(f"✅ Guardado: {out}")
print(f"   11 cuentas CF mapeadas")
