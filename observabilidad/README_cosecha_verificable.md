# Cosecha verificable desde los recursos existentes

Esta ruta reutiliza el inventario de `miu-ecosistema`, no crea cuentas ni requiere reconstruir el pool. Separa descubrimiento de catálogos, salud declarada, autenticación y capacidad de inferencia.

## Cosechar rutas públicas CF

```sh
python3 scripts/harvest_cf_public.py \
  --limit 96 \
  --output observabilidad/cf_public_harvest_20261108.json
```

El programa lee el inventario existente mediante el CLI GitHub conectado y fija el commit antes de obtener sus bytes. El inventario histórico contiene nombres, no disponibilidad actual; ROT13 se interpreta como codificación, no como cifrado.

Solo construye rutas `/health` para la asociación cuenta/dominio ya conocida de `jaimepvicente`. No adivina el dominio de la segunda cuenta, no usa claves CF, no sigue redirecciones y no ejecuta inferencias ni despliegues. Máximo cuatro solicitudes simultáneas, seis segundos por solicitud y 96 objetivos; cada resultado tiene fecha y alcance.

Un 401/403 se conserva como protegido. Un 404 solo indica que la ruta probada falta; no demuestra que el worker no exista. Un JSON `ok: true` se registra como salud declarada, nunca como cuota o inferencia verificadas.

## Validar las entradas del pool sin falsos positivos

Los dos workflows Python existentes ahora llaman a `scripts/llm_probe.py`, en lugar de mantener dos implementaciones divergentes. Conservan su origen de entradas y los nombres del archivo de salida y del contador `validas`; no se envían claves de prueba desde esta sesión.

```sh
python3 -m unittest discover -s scripts -p test_harvest_and_probe.py -v
```

- Una entrada puede declarar `provider`; los proveedores desconocidos o las claves ambiguas sin proveedor quedan como `provider_required`, sin tráfico.
- Un prefijo inequívoco solo elige un destino candidato. Nunca certifica que la clave funcione.
- Primero se consulta el catálogo sin credencial. Si ya es público, se cosechan sus modelos sin transmitir la clave y se devuelve `public_catalog`, `valid: false`.
- Solo tras el rechazo del control sin credencial se prueba la clave en ese mismo destino. No hay difusión de una clave a varios proveedores ni redirecciones.
- Un catálogo autenticado queda como `authenticated_catalog`. No certifica inferencia, saldo ni cuota.
- Un 401/403 o 429 termina la ruta. No se rota a otras cuentas para eludir un límite.
- El registro guarda ordinales, no prefijos de claves, alias privados, contenidos de excepciones ni secretos.

Los workflows conservan sus mecanismos históricos de lectura y reporte remoto, que no se han ejecutado ni certificado aquí. El módulo TypeScript legado `provider_probe.ts` tampoco queda desplegado o corregido por este cambio Python; sus consumidores deben migrar o recibir una revisión específica.

## Alcance de distribución

La rama y su pull request son una propuesta revisable. No se fusionan cambios automáticamente, no se habilita billing y no se inicia un despliegue de workers o edge functions; el único workflow nuevo ejecuta pruebas sintéticas sin claves.
