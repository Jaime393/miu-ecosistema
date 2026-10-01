# GAS MIU Mesh V270 — Distribución

Archivo de reemplazo para cualquier nodo GAS del mesh.

## Obtener el código

```bash
# Desde Termux o cualquier entorno:
curl -L https://raw.githubusercontent.com/Jaime393/miu-ecosistema/main/gas/MIU_MESH_V270.js
```

## Cómo aplicarlo

1. Abrir [script.google.com](https://script.google.com)
2. Proyecto existente (Pulse_v152, miu_mesh_v152, etc.) → borrar todo el contenido
3. Pegar el contenido del archivo
4. Correr `setupTodo()` una vez
5. Deploy → Web app → Ejecutar como: Yo → Acceso: Cualquiera → Deploy

## Qué resuelve respecto a V152

| Problema V152 | Solución V270 |
|---|---|
| phi hardcodeado (28.432) | Lee phi/rho/ciclo de Supabase fepyzx en tiempo real |
| Heartbeat siempre V152 | Escribe estado real del enjambre |
| Cron 30min | Cada 15min |
| Sin BCRP | fetchBCRP() → IPC + USD/PEN vivos |
| Sin /miu/status | Devuelve phi real con envelope completo |

## Drive original

`1cjBDCgK1lyyRgG5EEBSYk9P609oMzjlR` — heartbeat canónico  
`18A05RfRQRJj42ucEb8M9ELh5mu9TKSOC` — código fuente Drive

## Fuente de verdad para phi

```
GET https://tpfiybpguuxskitszhmk.supabase.co/functions/v1/contexto-global
  -H 'Authorization: Bearer ANON'
→ .vitales.phi  (phi operativo real)
```
