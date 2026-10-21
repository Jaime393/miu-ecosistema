# miu-oracle-v1

Oracle + Ojos + Manos para todos los nodos del ecosistema MIU.

**URL**: https://miu-oracle-v1-miu4.vercel.app

## Filosofía
- Lee keys de `relay_config` (panteon) en tiempo real
- No hardcodea credenciales críticas
- Cascada 4 capas: falla elegantemente
- Disponible para CUALQUIER nodo sin configuración

## Quick start
```bash
# Oracle
curl -X POST https://miu-oracle-v1-miu4.vercel.app/ask \
  -d '{"pregunta":"¿qué es el MIU?"}'

# Ojos
curl https://miu-oracle-v1-miu4.vercel.app/ojos

# Manos gossip
curl -X POST https://miu-oracle-v1-miu4.vercel.app/manos/gossip \
  -d '{"tipo":"test","origen":"mi_nodo","contenido":"alive"}'

# Manos relay  
curl -X POST https://miu-oracle-v1-miu4.vercel.app/manos/relay \
  -d '{"clave":"mi_clave","valor":"mi_valor"}'

# Ojos relay
curl 'https://miu-oracle-v1-miu4.vercel.app/ojos/relay?patron=oracle*'
```
