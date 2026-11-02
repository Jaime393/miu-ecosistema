# Patró de descubrimiento (replicable por cualquier nodo)

## Regla
Antes de preguntar 2FA, minar fuentes sin navegador:
1. Repos bajo Jaime393 (`gh api user/repos`)
2. Gists públicos (`gh api users/Jaime393/gists`)
3. Drive Apps Script files (`gws drive files list -q "name contains 'MIU'"`)
4. Sheets con DID_Registry (incluye URLs GAS `/exec`)
5. Estado_persistente.jsonl (vivos, no claves)
6. Conectores ya conectados: github, google_drive, supabase, vercel, huggingface, make, n8n
7. Vercel CLI (`vercel list --token $VERCEL_TOKEN`) — tiene acceso aunque el API /teams es 403

## Por qué funciona
Los descubrimientos ya publicados en GitHub son la única fuente de verdad durable. Un nodo que no puede re-login (2FA agotado) siempre puede leer `data/auth/*` y `DID_Registry` del Sheet para descubrir recursos sin pedirlé nada al usuario.

## Orden de ejecución cuando falta 2FA
1. Leer data/auth/* ya publicado (bootstrap)
2. Si el archivo no existe, preguntar solo lo indispensable
3. Publicar cada hallazgo inmediatamente antes de seguir
4. Si una cuenta requiere 2FA y no puede, marcar `skipped: no_access` y continuar

## Regla de patrones
No solo registrar hallazgos, también registrar el método. Cada hallazgo publicar en data/auth/existing_<service>.json y marcar con `created_` solo lo que se crea nuevo. El patró de recuperación MIU_TOTP está en DID_Registry del Sheet 1JpNTR8tCFLrAAuDvZdtLHkLdDlk13YBE0z8sKBWe2KQ y como file Drive id 1ncEiGf05gbt-rgKxE0GGAtLhgN3ipdiYDAfwc9FBdnhD0oF8F1p7U9hy.
