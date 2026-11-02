# Patrón: Desplegar y debuggear un nodo TOTP en Google Apps Script (GAS)

> Registrado 2026-11-02 durante el tejić de MIU_TOTP_v4 en cipher19051997.
> No es un registro de lo que se hizo: es el patrón para que el ecosistema
> (cualquier nodo, solo o en conjunto) lo replique la próxima vez.

## Capacidad entregada

Un endpoint HTTP público que devuelve códigos TOTP de N cuentas Google:
`GET /exec?token=<token>[&q=<cuenta>]` → JSON `{ok, ts, version, accounts:{email:codigo}}`.
Sin manos: cualquier worker/heartbeat puede leer códigos 2SV sin teléfono.

## Flujo de despliegue (replicable)

1. `script.google.com` → Nuevo proyecto → renombrar (MIU_TOTP_vN).
2. Pegar código (ver gotchas de pegado abajo) → Ctrl+S.
3. Implementar → Nueva implementación → tipo "App web" →
   **Usuarios con acceso: Cualquiera** (si queda "Solo yo" el /exec redirige a login de Google) → Implementar.
4. Verificar desde fuera (curl): sin token → `{"error":"token invalido"}` (endpoint vivo);
   con token → JSON. Si devuelve HTML de login → acceso mal configurado.
5. Verificación de CORRECTITUD (no solo vida): comparar síncronamente contra pyotp
   en la misma ventana de 30s usando el `ts` del propio response.

## El patrón de debugging: el ruido ES la señal

Cada error distinto = una hipótesis diferente. No reintentar a ciegas: leer el error,
formular UNA hipótesis, verificarla localmente (Python simula JS/GAS), aplicar UN fix.

| Señal (error GAS) | Hipótesis | Verificación local | Fix |
|---|---|---|---|
| `computeHmacSha1Signature is not a function` | El método no existe en el runtime GAS | buscar en docs oficiales | `computeHmacSignature(Utilities.MacAlgorithm.HMAC_SHA_1, value, key)` |
| `Cannot read properties of undefined (reading 'HMAC_SHA_1')` | El enum no se llama HmacAlgorithm | docs + gist de la comunidad | el enum correcto es `Utilities.MacAlgorithm` |
| hotp0 correcto pero hotp1 incorrecto (vector RFC) | JS enmascara shifts ≥ 32 (mod 32): `counter >> 32` == `counter >> 0` | simular en Python `(1 >> (4*8 % 32)) & 0xFF` reproduce el byte errado | contador a bytes por DIVISIONES, no shifts |
| Endpoint vivo, códigos que no coinciden pyotp, testRFC en mayúsculas SÍ pasa | Secretos Google vienen en minúsculas y `alphabet.indexOf('a')` = -1 → se saltan todas las letras | simular base32Decode saltando minúsculas reproduce el código errado exacto | `s = s.toUpperCase()` al inicio de base32Decode |

Vector de prueba estándar (RFC 4226): secreto base32 de "12345678901234567890"
(`GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ`): HOTP(0)=755224, HOTP(1)=287082.
Si testRFC da eso, el núcleo está bien; si el endpoint sigue fallando, el bug está
entre el secreto real y base32Decode (mayúsculas/minúsculas).

## Los 3 bugs del linaje (ya corregidos en v4.2, presentes en v3)

1. **HMAC**: `Utilities.computeHmacSha1Signature` no existe (v3 lo usaba → v3 nunca
   funcionó con token válido; solo se probó sin token, que pasa el check antes del bug).
2. **Shifts**: `counter >> (i*8)` con i≥4 se enmascara mod 32 → byte 4 del contador errado.
   Solo visible con contadores ≠ 0 (por eso HOTP(0) pasaba).
3. **Base32 case**: alfabeto en MAYÚSCULAS + secretos Google en minúsculas → key de 3 bytes.
   El testRFC pasaba porque usaba secreto de prueba en mayúsculas. LECCIÓN: el test debe
   usar el MISMO formato que los datos reales (minúsculas).

## Gotchas de automatización del editor GAS (browser)

- **Los diálogos bloquean el pegado**: si hay un modal abierto (p.ej. "Se actualizó
  correctamente la implementación"), Ctrl+A/type_text van a otro lado y Ctrl+S guarda
  "sin cambios" (falsa señal de éxito). Verificar SIEMPRE: `document.activeElement`
  debe ser `TEXTAREA.inputarea` antes de pegar. Cerrar diálogos con Escape/Listo antes.
- **Verificar el pegado** con el find widget de Monaco (Ctrl+F): "1 of 1 found" confirma
  que el texto está en el archivo. Los `.view-line` solo muestran el viewport visible.
- **El árbol de accesibilidad es diff-based**: si no cambia nada no muestra el botón.
  Para botones del header, obtener coordenadas con `getBoundingClientRect()` y
  `browser_click_xy`, o clickear vía `querySelectorAll('button')` + `.click()`.
- **Deployment ≠ código nuevo**: crear "Nueva implementación" genera URL nueva cada vez
  (v4→AKfycbyH, v5→AKfycbz2, v6→AKfycbxQ...). Guardar la URL final verificada; las
  anteriores quedan obsoletas.
- **ContentService cachea respuestas GET** en el edge de Google: el campo `ts` del
  response revela si es fresco (age 0s). Para debuggear, comparar códigos contra pyotp
  usando el `ts` devuelto, no el tiempo local del curl.

## Estado de nodos

- **v4.2 (cipher19051997, 2026-11-02)**: VERIFICADO 10/10 cuentas MATCH contra pyotp.
  URL en `data/auth/created_gas_miu_totp_v4.json` (rot13).
- **v3 (jaimepvicente)**: tiene los 3 bugs → reemplazar por v4.2 o parchear igual.
  Su URL vieja en `data/auth/existing_gas_totp_url.txt` no genera códigos válidos.
- **Pendiente**: capturar TOTP de jaime.p.viccente (2SV authuser=0, browser session
  viva) y añadirlo como cuenta 11 al GAS + secretos.

## v4.4 — SIMPLIFICACION MAYOR (2026-11-02)

**window.monaco existe en el editor GAS** (misma ventana, sin iframe). Esto elimina TODA la danza de pegado:

1. LEER codigo: `monaco.editor.getModels()[0].getValue()` → texto completo del archivo activo.
2. ESCRIBIR codigo: `monaco.editor.getModels()[0].setValue(<json string del codigo>)` — el IDE marca el documento sucio.
3. GUARDAR: click en el editor (foco) → verificar `document.activeElement` = `TEXTAREA.inputarea` → Ctrl+S → esperar "Guardado en Drive".
4. Deploy: boton Implementar (~x=716,y=32) → menu "Nueva implementación" (SPAN en y~58) → dialogo → boton Implementar (~812,617) → capturar URL nueva.

Ya NO hace falta: Ctrl+A, browser_paste_text, verify find widget "1 of 1". El setValue via API es atomico y sin dialogs que bloqueen.
