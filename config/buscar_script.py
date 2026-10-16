"""
Busca un script en todas las carpetas probables del micelio.
Uso: python3 buscar_script.py tejedor
"""
import sys, subprocess
from pathlib import Path

if len(sys.argv) < 2:
    print("Uso: buscar_script.py <nombre_parcial>")
    sys.exit(1)

needle = sys.argv[1]
roots = [
    Path.home(),
    Path.home() / "miu-ecosistema",
    Path.home() / "miu_slim",
    Path.home() / "miu-relay",
    Path.home() / "miu",
    Path.home() / ".miu",
]

hits = []
for root in roots:
    if not root.exists():
        continue
    try:
        for p in root.rglob(f"*{needle}*"):
            if p.is_file() and p.suffix in (".py", ".sh", ".js", ".ts"):
                hits.append(str(p))
    except (PermissionError, OSError):
        pass

if hits:
    for h in hits[:20]:
        print(f"✅ {h}")
else:
    print(f"❌ No encontrado: {needle}")
