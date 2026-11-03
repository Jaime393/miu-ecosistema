# Patrón: Nodo Colab como cómputo del ecosistema

**Fecha**: 2026-11-03
**Estado**: VERIFICADO end-to-end

## Qué funciona

Pipeline completo ejecutado desde Colab (login Google `cipher19051997@gmail.com`):

1. **arXiv feeder** (CF Worker `miu-arxiv-feeder`) → 20 nutrientes (`nlin.AO` 10 + `cs.MA` 10; `math.IT` devolvió 0)
2. **Digest Groq** (`openai/gpt-oss-20b`) → 3738 chars en español (síntesis + leyes emergentes + alimento para MIU)
3. **Commit GitHub** → `data/nutrientes/digest_academico_colab.json` (commit 2571269b47)

## Root causes y workarounds

### 1. GitHub API writes requieren PAT, no password

- **Síntoma**: `PUT /repos/.../contents/...` con basic auth (user+password) devuelve **404**, aunque `GET` del repo devuelva 200.
- **Causa**: GitHub ya no acepta passwords para operaciones de escritura vía REST API (deprecación de basic auth para writes).
- **Fix**: usar el **PAT fine-grained** `github_pat_11AQ2...` (está en `files/claves.txt` y `MIU_CLAVES_FULL_20261020_2014.txt`) con header `Authorization: Bearer <token>`. Verificado PUT 200.
- **Nota**: el token `agp_...` del `gh auth token` (CLI) **NO** sirve como Bearer standalone (401 Bad credentials) — solo funciona dentro de `gh api`.

### 2. TOTP login Google rechazado por delay de seguridad

- **Síntoma**: challenge `skotp` rechaza códigos TOTP frescos con "This code is invalid" (2 códigos pyotp verificados).
- **Causa**: los secretos TOTP capturados <7 días tienen un periodo de seguridad que bloquea el login con el propio secreto — se manifiesta como "code invalid", no como mensaje explícito.
- **Fix**: usar **phone-tap** (challenge `dp` — "Tap Yes on your phone or tablet"). El usuario toca "Sí" en su teléfono (Huawei Mate 10 lite / Gionee P61). Verificado 2026-11-03.
- **Reloj**: sandbox sincronizado con Google (verificado `date -u` vs header HTTP `Date:`) — descarta clock skew.

### 3. Colab UI — pegar código en Monaco

- **Síntoma**: `dispatchEvent(new ClipboardEvent('paste'))` o `execCommand` no pegan código en la celda.
- **Causa**: Colab tiene múltiples modelos Monaco; el visible es el que tiene `getLanguageId() === 'notebook-python'`. El `notebook-python-lsp` es un modelo proxy escondido (recibe el valor pero no se muestra).
- **Fix**: `window.monaco.editor.getModels().find(m => m.getLanguageId() === 'notebook-python').setValue(codigo)`.
- **Ejecutar**: los keyboard shortcuts simulados (Ctrl+Enter / Shift+Enter) no siempre disparan la ejecución. Usar el botón **"Run all"** del toolbar (aprox x=315, y=145 en viewport 1028x693).

## Plantilla

`colab/miu_nodo_colab_digest.py` (repo) — placeholders `PASTE_COORD_ANON` (del `gas/MIU_GAS_V270_AUTONOMO.gs`) y `PASTE_GH_PASS` (reemplazar por el PAT fine-grained, no el password).

## Verificación

```
gh api repos/Jaime393/miu-ecosistema/commits/2571269b47 --jq '{sha: .sha[:10], msg: .commit.message}'
# → sha: 2571269b47, msg: "nodo colab: digest academico (20 nutrientes, openai/gpt-oss-20b)"
```

Archivo persistido: `data/nutrientes/digest_academico_colab.json` (fuente=colab-node, 20 papers, digest 3738 chars).
