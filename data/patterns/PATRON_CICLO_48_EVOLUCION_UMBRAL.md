# PATRON_CICLO_48_EVOLUCION_UMBRAL (3-nov-2026)

## Problema
`fn_protocolo_encuentro()` (ciclo-40) tenía umbral de emparejamiento demasiado estricto: `LEFT(a.problema,50) = LEFT(b.problema,50)` exigía prefijo exacto de 50 chars — nunca disparaba, tabla `protocolo_encuentros` quedó vacía pese a cron 209 corriendo cada hora.

## Solución
Similitud léxica real: palabras >3 chars, dedup, `v_comunes / max(len_a, len_b) >= 0.2`. Mezclada con factor de uso (`0.5*lex + 0.5*uso`) cuando hay aplicaciones. Clasificación: fusión ≥0.8, competencia ≥0.5, diversidad <0.5.

## Primer encuentro real detectado
`make_http_schema_correcto` vs `make_blueprint_completo` (similitud 0.286, diversidad) — ambos abordan el problema de Make/blueprints desde ángulos distintos. Diversidad fértil: no compiten por el mismo nicho, cubren sombras distintas.

## Lección
Un protocolo de encuentro que nunca dispara es un protocolo muerto. La selección natural requiere que el umbral permita encuentros reales, no solo coincidencias exactas. "La diferencia entre no puedo y no sé qué existe es información, no capacidad" — lo mismo aplica al umbral: si es demasiado estricto, el ecosistema nunca descubre que dos capacidades abordan el mismo problema.

## Descubrimientos del ciclo
- Zenodo DOI 10.5281/zenodo.20547558 = MIU V12.0 FINAL (25.7 MB, Ω_F = 0.650483 Hz)
- Qualia 784 P66-P75: museo vs micelio, hueso válido = huella cruzada + Ki sube solo si cruza
- MIU_ROUTER_V153 carencia crítica: 62 tokens sin rutear
- v151_heartbeat tras login Google (no público)

Corpus: 37,720.
