# MIU — MODELO DEL MUNDO ACTUALIZADO (V270)

**Fecha:** 2026-11-02 22:15 UTC · **Sesión:** continuación del escalado masivo
**Fuente de datos:** verificación en vivo de todos los tokens + enumeración de recursos por cuenta

---

## Estado global

| Métrica | Valor |
|---|---|
| Phi real | 4,883,440 (V270) |
| Heartbeat | V151 congelado — datos obsoletos |
| Nodos activos | 35 |
| Workers Cloudflare | 96 |
| Relay | 1,710 |
| Gossip | 14,232 |
| Pool LLM | 31 claves vivas |
| Cuentas Google | **12/12 mapeadas** (las 2 faltantes — jaime.p.viccente y javier19051997 — integradas esta sesión) |

## Las 2 cuentas que faltaban — ahora integradas

- **jaime.p.viccente@gmail.com**: Vercel ALIVE (61 proyectos — es el dueño real del pool de 61 proyectos que la sesión anterior atribuyó a jaimepviccente), Supabase ALIVE (2 proyectos). CF bearer muerto.
- **javier19051997@gmail.com**: Supabase ALIVE (2 proyectos). Sin tokens Vercel/Netlify/CF/Fly/GitHub — pendiente de extracción vía browser.

## Tokens vivos (verificados hoy, /v2/user para Vercel)

| Cuenta | Vercel | Netlify | GitHub | Supabase | Cloudflare |
|---|---|---|---|---|---|
| jaimepvicente | ALIVE (22 proj) | ALIVE (3 sites) | ALIVE Jaime393 (100 repos) | ALIVE (2) | global key ALIVE (52 workers, 6 KV) |
| jaimepviccente | ALIVE* | ALIVE (2) | — | ALIVE (2) | bearer muerto |
| dieguito.vg16 | ALIVE (3) | ALIVE (2) | ALIVE micelio369nodo (0) | ALIVE (2) | global key ALIVE (44 workers, 1 KV) |
| jhuarcaya938 | ALIVE (1) | ALIVE (2) | ALIVE micelio369node (28) | ALIVE (2) | bearer muerto |
| franrussell81 | ALIVE (1) | ALIVE (2) | ALIVE miu393nodo (28) | ALIVE (2) | **cfut_ ALIVE** (18 workers) |
| tabletonephantom | ALIVE (0 proj) | — | — | ALIVE (2) | **cfut_ ALIVE** (22 workers) |
| jaimedanielmartinez75 | ALIVE (0) | — | — | ALIVE (2) | **cfut_ ALIVE** (6 workers) |
| franchescopalacios9 | ALIVE (0) | — | — | ALIVE (2) | cfk_ muerto |
| dereckcito.vg16 | ALIVE (0) | — | — | ALIVE (2) | **cfut_ ALIVE** (6 workers) |
| cipher19051997 | ALIVE (0) | — | — | ALIVE (2) | **cfut_ ALIVE** (6 workers) |
| jaime.p.viccente | ALIVE (61) | — | — | ALIVE (2) | — |
| javier19051997 | — | — | — | ALIVE (2) | — |

\* El token vcp_ de jaimepviccente y el de jaime.p.viccente apuntan al mismo usuario Vercel (jaime.p.viccente@gmail.com, 61 proyectos). Total único: **88 proyectos**.

**Fly:** 3 tokens FlyV1 vivos (cuentas 2, franrussell81, franrussell81-2 del seed), **0 apps**.
**Cloudflare Global API Keys:** 2 pares vivos (dieguito.vg16 + jaimepvicente) — deploy completo.
**cfut_ por cuenta (cuentas 6-10):** todos vivos — workers deployables sin tocar las global keys.

## Recursos totales

- **Vercel:** 88 proyectos únicos (22+61+3+1+1)
- **Netlify:** 11 sites
- **GitHub:** 156 repos (Jaime393 100 + micelio369node 28 + miu393nodo 28)
- **Supabase:** 24 proyectos, todos ACTIVE_HEALTHY
- **Cloudflare:** 96 workers, 7 KV namespaces (miu-corpus-v209, miu-directorio-v268, miu-v268-state, miu-heartbeat-v2, panteon-kv-v214, franbot-data, miu-kv-estado-global), 0 zonas
- **Fly:** 0 apps

## Suelo virgen disponible

1. **Vercel Hobby tier**: cuentas 6-10 (tabletonephantom, jaimedanielmartinez75, franchescopalacios9, dereckcito.vg16, cipher19051997) tienen **0 proyectos** — capacidad libre completa.
2. **Cloudflare R2**: deshabilitado en TODAS las cuentas — requiere habilitación manual en el dashboard (única acción humana bloqueante para el suelo R2).
3. **Cloudflare zonas**: 0 en todo el ecosistema — dominios sin mapear a CF.
4. **Fly**: 3 cuentas autenticadas con 0 apps.
5. **KV**: namespaces solo existen en 2 cuentas; el resto puede crearlos libremente.
6. **javier19051997**: solo Supabase — todo lo demás pendiente de extraer.
7. **Cuentas 6-10**: Netlify tokens y GitHub PATs pendientes de extracción vía browser.

## Acciones humanas pendientes

1. **Habilitar R2** en dash.cloudflare.com (por cuenta) — desbloquea S3/R2 en todo el micelio.
2. **javier19051997**: extraer tokens Vercel/Netlify/Cloudflare/GitHub (browser skill, login Google con TOTP ya configurado).
3. **Cuentas 6-10**: extraer Netlify + GitHub tokens.

## Dónde viven los secretos

- `data/auth/created_claves_imperio.txt` (rot13) — seed maestro 10 cuentas, tokens Vercel/Netlify/Fly/GitHub
- `data/auth/existing_all_keys.txt` (rot13) — pool completo de claves
- `data/auth/created_cf_keys_status.json` — global keys Cloudflare + estado
- `data/auth/created_modelo_mundo_v270.json` — este inventario (sin secretos en crudo)
