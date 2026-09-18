#!/bin/bash
# MIU v11.3 Git + Wrangler + Terraform FIXED - Termux / Ubuntu
# Fix: fatal not a git repository + wrangler loop + terraform not found

set -e
echo "ρ(x)>0 MIU v11.3 git + wrangler + terraform fix"

# 1. Git init fix
if [ ! -d ".git" ]; then
  echo "No git repo, iniciando..."
  git init
  git config user.email "jaimepvicente@miu.local" || true
  git config user.name "Fran MIU" || true
  echo "# MIU v11.3" > README.md
  echo "node_modules/" > .gitignore
  echo ".wrangler/" >> .gitignore
  git add .
  git commit -m "v11.2 router 62 tokens Φ168→500" || echo "Commit fail, checking status"
else
  echo "Git repo exists"
  git status --short
fi

# Remote check
if ! git remote | grep -q origin; then
  echo "Añadiendo remote origin (reemplaza con tu repo)..."
  echo "git remote add origin https://github.com/jaime393/miu-ecosistema.git"
  # git remote add origin https://github.com/jaime393/miu-ecosistema.git
else
  git remote -v
fi

# 2. Wrangler fix - evita loop Ok to proceed? (y)
echo "Instalando wrangler sin prompt..."
npm install -g wrangler@4.134.0 --yes || npm install -g wrangler --yes || yarn global add wrangler || echo "npm fail, usando npx"

# Usa npx para evitar instalación global loop
echo "Probando npx wrangler --version..."
npx wrangler --version || echo "Wrangler no disponible, instalar con: npm i -g wrangler"

# 3. Terraform fix - no existe en Termux, usar OpenTofu o Docker
if ! command -v terraform >/dev/null 2>&1; then
  echo "Terraform not found, instalando OpenTofu (fork libre) o usando Docker..."
  # Opción A: OpenTofu
  if command -v pkg >/dev/null 2>&1; then
    pkg install -y opentofu || echo "pkg opentofu fail"
  elif command -v apt >/dev/null 2>&1; then
    curl -fsSL https://get.opentofu.org/install-opentofu.sh | sh || echo "OpenTofu install fail"
  fi
  
  # Opción B: Docker (si existe)
  if command -v docker >/dev/null 2>&1; then
    echo "Usando Docker para terraform: docker run --rm -v $(pwd):/app -w /app hashicorp/terraform init"
  else
    echo "Terraform/OpenTofu no disponible en este entorno, usar Oracle Cloud Shell o GitHub Actions"
    echo "Alternativa: terraform en GitHub Actions - ver .github/workflows/miu_v11_2_r2_kv_fix.yml"
  fi
else
  terraform --version
fi

# 4. bc fix - no existe en Termux minimal, usar python3
if ! command -v bc >/dev/null 2>&1; then
  echo "bc not found, usando python3 para cálculos Φ_ruta (fix aplicado en router_darwiniano_v11_3_FIXED.sh)"
  python3 --version
fi

# 5. Git add + commit + push con manejo de errores
echo "Git add . && commit && push..."
git add . || echo "git add fail"
git commit -m "v11.3 fix router sin bc + curl rutas absolutas + git init + wrangler npx + terraform opentofu Φ168→500" || echo "Nada para commitear o commit fail"

if git remote | grep -q origin; then
  git push -u origin main || git push || echo "Push fail - verifica token GITHUB_TOKEN"
else
  echo "Sin remote origin, no se puede push. Añade: git remote add origin https://github.com/jaime393/miu-ecosistema.git"
fi

echo "Fix completado - v11.3 listo"
