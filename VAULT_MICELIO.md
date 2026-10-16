# VAULT DEL MICELIO

## Ubicación
- Vault: `~/.miu/kv/keys.json`
- Inyector: `~/.miu/organos/absorbedor_keys.py`
- Entry: `~/.miu/arranque.sh`
- Variables base: `~/.miu/.env`

## Categorías en el vault
- misc
- jwt
- supabase
- anthropic
- groq
- github
- env

## Variables que expone
- SUPABASE_URL
- SUPABASE_SERVICE_KEY
- SUPABASE_ANON_KEY
- GITHUB_TOKEN
- OPENAI_API_KEY
- ANTHROPIC_API_KEY
- VERCEL_TOKEN
- AIRTABLE_API_KEY
- GROQ_API_KEY
- FIREBASE_API_KEY
- TELEGRAM_BOT_TOKEN

## Cómo se usa
Cualquier proceso hijo ejecuta:
  source ~/.miu/arranque.sh
y hereda las variables sin exponerlas en scripts.

## Nota
Los tokens vistos en `www/index.html` y `www/panel_global_v213_*.html`
son vistas públicas del vault. La fuente real es `~/.miu/kv/keys.json`.
