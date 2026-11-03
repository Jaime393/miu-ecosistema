#!/usr/bin/env python3
"""cable_razonador — interfaz única. Cualquier módulo importa `pensar`."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from razonador import razonar

def pensar(prompt, contexto=""):
    """Devuelve texto limpio o 'SIN_RESPUESTA: motivo'."""
    entrada = f"{contexto}\n\nPREGUNTA:\n{prompt}" if contexto else prompt
    r = razonar(entrada)
    if r.get("ok"):
        return r["respuesta"]
    return f"SIN_RESPUESTA: {r.get('error', 'desconocido')}"

def pensar_json(prompt, contexto=""):
    """Devuelve dict completo: {ok, servicio, respuesta, error}."""
    entrada = f"{contexto}\n\nPREGUNTA:\n{prompt}" if contexto else prompt
    return razonar(entrada)
