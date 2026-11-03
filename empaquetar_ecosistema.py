#!/usr/bin/env python3
"""empaquetar_ecosistema — junta los .py/.sh/.json/.md del ecosistema en un zip."""
import hashlib, json, os, zipfile, datetime
from pathlib import Path

HOME = Path("/data/data/com.termux/files/home")
SD = Path("/storage/25A9-180D")
DL = Path("/storage/emulated/0/Download")

FUENTES = [
    ("core",           HOME / "miu-ecosistema"),
    ("oraculo_engine", HOME / "miu" / "oraculo"),
    ("miu_state",      HOME / "miu" / "state"),
    ("miu_scripts",    HOME / "miu"),
    ("flex_primary",   SD / "biblioteca_miu/todo/miu-ecosistema/modulos/flex"),
    ("flex_backup",    SD / "miu-brain-backup/miu-ecosistema/modulos/flex"),
    ("miu_base",       SD / ".miu-base"),
]

INCLUIR = {".py", ".sh", ".json", ".md", ".env", ".conf", ".txt", ".toml"}
SKIP_DIRS = {"__pycache__", ".git", "node_modules", "venv", ".venv", "cache"}
SKIP_FILES = {"contexto_miu.json", "contexto_miu.md"}
EXCLUIR_SUFIJOS = (".bak", ".log", ".jsonl", ".db", ".sqlite", ".gguf", ".pem", ".key", ".pid")
MAX_SIZE = 500_000

def quick_hash(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        h.update(f.read(8192))
    return h.hexdigest()[:16]

def main():
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre = f"miu_ecosistema_{ts}.zip"
    destino = DL / nombre

    print(f"═══ EMPAQUETANDO ECOSISTEMA ═══\n")
    print(f"Destino: {destino}\n")

    manifest = []
    por_fuente = {}
    for alias, fuente in FUENTES:
        if not fuente.exists():
            print(f"  ⚠️  {alias}: no existe {fuente}")
            continue
        n = 0
        for root, dirs, files in os.walk(fuente):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for name in files:
                p = Path(root) / name
                if p.suffix not in INCLUIR: continue
                if p.name in SKIP_FILES: continue
                if any(name.endswith(s) for s in EXCLUIR_SUFIJOS): continue
                try:
                    st = p.stat()
                    if st.st_size > MAX_SIZE: continue
                except: continue
                try:
                    rel = p.relative_to(fuente)
                except:
                    rel = Path(name)
                arcname = f"{alias}/{rel}"
                manifest.append({
                    "arcname": arcname,
                    "origen": str(p),
                    "size": st.st_size,
                    "mtime": st.st_mtime,
                    "sha256_8k": quick_hash(p),
                })
                n += 1
        if n:
            por_fuente[alias] = n
            print(f"  ✅ {alias:15} {n:4} archivos")

    manifest.sort(key=lambda x: x["mtime"], reverse=True)
    total_size = sum(m["size"] for m in manifest)
    print(f"\nTotal: {len(manifest)} archivos, {total_size // 1024} KB fuente\n")

    readme = f"""MIU ECOSISTEMA — snapshot {ts}
======================================

Este zip contiene los archivos fuente del ecosistema MIU.

Contenido ({len(manifest)} archivos):
"""
    for alias, n in por_fuente.items():
        readme += f"  - {alias:15} ({n} archivos)\n"
    readme += f"""
Total fuente: {total_size // 1024} KB
Generado: {datetime.datetime.now().isoformat()}

Manifest completo: manifest.json
  - ordenado por fecha de modificación (más reciente primero)
  - incluye sha256 de primeros 8KB de cada archivo
  - incluye ruta origen real en el dispositivo

ADVERTENCIA:
  Este zip contiene credenciales en texto plano
  (.netrc, .env, tokens en miu_base/).
  Manejar con cuidado.

Reconstrucción:
  cp -r core/* ~/miu-ecosistema/
  cp -r flex_primary/* /storage/25A9-180D/biblioteca_miu/todo/miu-ecosistema/modulos/flex/
  cp -r flex_backup/* /storage/25A9-180D/miu-brain-backup/miu-ecosistema/modulos/flex/
  cp -r miu_base/* /storage/25A9-180D/.miu-base/
"""

    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for m in manifest:
            try:
                zf.write(m["origen"], m["arcname"])
            except Exception as e:
                print(f"  ⚠️  skip {m['arcname']}: {e}")
        zf.writestr("README.txt", readme)
        zf.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))

    final_size = destino.stat().st_size
    print(f"═══ ZIP CREADO ═══")
    print(f"  {destino}")
    print(f"  {final_size // 1024} KB (comprimido)")
    print(f"  {len(manifest)} archivos empaquetados")
    print(f"\n📂 Abrir carpeta: termux-open {DL}")
    print(f"📤 Compartir:     termux-share {destino}")

if __name__ == "__main__":
    main()
