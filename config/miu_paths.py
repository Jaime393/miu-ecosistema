"""
miu_paths.py — Inyector de rutas flexibles del micelio (versión Python).
Uso:
    from miu_paths import MIU_ECOSISTEMA, MIU_VAULT, path
    print(MIU_ECOSISTEMA)
    # O busca flexible:
    ruta = path("MIU_SUELO_GRACE")
"""
import json
import os
from pathlib import Path

_DEFAULT_JSON = Path.home() / "miu-ecosistema" / "config" / "paths.json"


def _load_paths(json_file=None):
    jf = Path(json_file) if json_file else _DEFAULT_JSON
    if not jf.exists():
        raise FileNotFoundError(f"paths.json no encontrado en {jf}")
    with open(jf) as f:
        return json.load(f).get("paths", {})


def path(name, json_file=None):
    """Devuelve la primera ruta existente para 'name'. None si ninguna existe."""
    paths = _load_paths(json_file)
    info = paths.get(name)
    if not info:
        raise KeyError(f"Variable desconocida: {name}")
    candidates = [info.get("primary", "")] + info.get("fallbacks", [])
    for c in candidates:
        if c and Path(c).exists():
            return c
    return None


def all_paths(json_file=None):
    """Devuelve dict {nombre: ruta_real_o_None}."""
    paths = _load_paths(json_file)
    result = {}
    for name, info in paths.items():
        candidates = [info.get("primary", "")] + info.get("fallbacks", [])
        found = None
        for c in candidates:
            if c and Path(c).exists():
                found = c
                break
        result[name] = found
    return result


# Exponer constantes al importar (todas en mayúsculas del JSON)
_paths = all_paths()
for _name, _val in _paths.items():
    globals()[_name] = _val

# Poner a disposición un helper de log con fallback
def log_file(name="MIU_LOGS", filename="miu.log"):
    """Devuelve ruta completa a un archivo de log, usando el primer dir existente."""
    d = path(name) or "/tmp"
    return os.path.join(d, filename)


if __name__ == "__main__":
    for name, p in _paths.items():
        status = "✅" if p else "❌"
        print(f"{status} {name} = {p}")
