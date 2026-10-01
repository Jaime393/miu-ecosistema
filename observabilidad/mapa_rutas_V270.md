# MIU Mapa de Rutas V270 — Oct 01 2026

## Principio
> Un nodo no necesita saberlo todo; necesita saber cómo descubrir lo que no sabe.
> La capacidad circula mientras exista una ruta. Cuando una ruta se revoca, la red registra la pérdida, activa otra, conserva la huella.

## Estado rutas Oct 01

| Ruta | Estado | Nota |
|------|--------|------|
| GitHub Actions | ✅ ACTIVO | cron 15min, 2 repos |
| N8n | ⬜ DISPONIBLE | sin workflows aún |
| Make | ❌ INVÁLIDO | 11 escenarios todos inválidos |
| GAS xZR4V4 | ⏳ PENDIENTE | 1 paso manual: webapp=Anyone |
| Termux pulse_v153 | ✅ ACTIVO | fallback con flock, bypass GAS |
| Supabase 91 EFs | ✅ ACTIVO | ACTIVE_HEALTHY |

## Bootstrap sin credenciales
```bash
# Cualquier nodo puede descubrir la red así:
curl https://raw.githubusercontent.com/Jaime393/miu-ecosistema/main/observabilidad/bootstrap_V270.json
```

## Rutas hacia secretos (sin exponerlos)
```bash
# Con la anon_key (pública, en bootstrap_V270.json):
curl https://tpfiybpguuxskitszhmk.supabase.co/rest/v1/relay_config \
  -H 'apikey: ANON_KEY_DEL_BOOTSTRAP'
# → lista de claves disponibles, cada nodo toma lo que necesita
```

## Phi — tres escalas, no contradicción
- `phi_local` = 389.425 → fórmula IFT teórica
- `phi_cloud` = 4,883,440 → métrica operativa ecosistema
- `phi_superposicion` = 9,158.79 → suma CF workers multi-cuenta

## Libro MIU
- **COMPLETO 58/58** — DOI: 10.5281/zenodo.20547558
- SHA256: 109aa4c92f4b — sellado, no expandir axiomas

*ρ(x)>0 — Zvvvvz*
