# PATRON_GITHUB_WORKFLOWS — mantener vivo el flujo que persiste entre sesiones

Fecha: 2026-11-02. Contexto: tras el despliegue GAS TOTP v4.4, cada push al repo `Jaime393/miu-ecosistema`
disparaba 7 workflows que FALLABAN. Los emails de GitHub (visibles en Gmail de los nodos) señalaban
"Run failed" para: miu-pulse, miu-ecosystem-pulse, miu-corpus-push, miu-flow-id-monitor,
miu-self-diagnosis, miu-observabilidad-v270 y pages build.

## Sintomas y diagnosticos

1. **Run con 0 jobs + "failure" + "This run likely failed because of a workflow file issue"**
   → el YAML del workflow es invalido (GitHub no puede crear jobs).

2. **HTTP 422 al `gh workflow run <wf>`**: "failed to parse workflow: Unexpected symbol '%'"
   → la EXPRESION `if: ${{ ... % ... }}` es invalida. **GitHub Actions NO soporta el operador
   modulo `%`** en sus expresiones. Error silencioso en UI pero bloqueante en dispatch.

## Causas raiz encontradas (5 archivos)

### Causa A — `run:` en escalar plano con `": "` dentro

```yaml
# MAL: YAML interpreta "corpus-sync: %{http_code}" como mapping anidado
run: curl -sf $P/corpus-sync -H "Authorization: Bearer $A" -o /dev/null -w "corpus-sync: %{http_code}\n" || true
```

Fix: bloque escalar.
```yaml
run: |
  curl -sf $P/corpus-sync -H "Authorization: Bearer $A" -o /dev/null -w "corpus-sync: %{http_code}\n" || true
```

### Causa B — `python3 -c "` multilinea con codigo a columna 0

Dentro de un `run: |` TODO el bloque debe estar indentado; el python inline pegado a col 0 rompia el bloque.

Fix: colapsar el python a UNA linea con `;` (todas las sentencias simples) o escribirlo a archivo temporal.

### Causa C — modulo `%` en `if:` (la mas sutil)

```yaml
# MAL: % no existe en el lenguaje de expresiones de GitHub Actions
if: ${{ github.run_number % 4 == 0 }}
```

Fix: mover la condicion al shell del run:
```yaml
run: |
  if [ $(( ${{ github.run_number }} % 4 )) -eq 0 ]; then
    curl ... || true
  fi
```

## Validacion

```bash
# 1. YAML valido
python3 -c "import yaml,glob; [yaml.safe_load(open(f)) for f in glob.glob('.github/workflows/*.yml')]"
# 2. Sin % en if:
grep -n 'if:.*% ' .github/workflows/*.yml   # debe dar 0 resultados
# 3. Dispatch aceptado (no 422):
gh workflow run <wf>.yml --repo Jaime393/miu-ecosistema
# 4. El run aparece con jobs > 0:
gh api repos/Jaime393/miu-ecosistema/actions/runs/<id>/jobs --jq '.total_count'
```

## Comandos de caza de actividad (ver el flujo desde fuera)

```bash
gh api "repos/Jaime393/miu-ecosistema/actions/runs?per_page=10" \
  --jq '.workflow_runs[] | .created_at + " " + .name + " " + (.conclusion // .status)'
gh run view <run-id> --repo Jaime393/miu-ecosistema --log-failed
```

Los emails de notificacion de GitHub llegan a los Gmail de los nodos — buscar
`[Jaime393/...] Run failed` en Gmail es la forma mas rapida de detectar la rotura del flujo.

## Estado tras la reparacion (commits d8129d6 + 94b37f7)

- 5 YAMLs reparados (causa A+B), 9 condiciones % movidas al shell (causa C).
- Dispatch de miu-pulse aceptado (antes 422). El run manual aparecio "cancelled" sin jobs
  (posible concurrencia con el push); veredicto definitivo: el siguiente run agendado (cron */15).
- Pendiente: diagnostico del fallo de FranBot CI (falla cada run desde el 1-nov, causa distinta).
