# Un harness mínimo de ingeniería

Este repositorio es un punto de partida copiable para un sistema operativo de proyecto ligero, construido alrededor de:

- `AGENTS.md` como guía de bootstrap para agentes.
- `memory-bank/` como fuente de verdad actual del proyecto.
- `evolution/` como historial versionado de cambios de dirección.
- harnesses de ejecución como comandos repetibles que demuestran que el software funciona.
- harnesses de evaluación de modelos como evaluaciones repetibles que miden comportamiento asistido por modelos.

El objetivo no es aumentar el volumen de documentación. El objetivo es dar a personas y agentes el mismo manual operativo compacto, y luego conectar ese manual con harnesses ejecutables.

## Qué hay en este repositorio

Archivos de ejemplo a nivel de proyecto:

- [AGENTS.md](AGENTS.md)
- [memory-bank/product.md](memory-bank/product.md)
- [memory-bank/architecture.md](memory-bank/architecture.md)
- [memory-bank/tech-stack.md](memory-bank/tech-stack.md)
- [memory-bank/milestone.md](memory-bank/milestone.md)
- [memory-bank/status.md](memory-bank/status.md)
- [evolution/prompt-v1.md](evolution/prompt-v1.md)
- [evolution/result-v1.md](evolution/result-v1.md)

Archivos de ejemplo a nivel de cuenta de usuario:

- [.local/bin/tackle-memory-bank-api-loop](.local/bin/tackle-memory-bank-api-loop)
- [.codex/prompts/tackle-next-memory-bank-todo.md](.codex/prompts/tackle-next-memory-bank-todo.md)

Referencias de harness:

- [Harness de ejecución](docs/EXECUTION_es.md)
- [Harness de evaluación de modelos](docs/MODEL_EVAL_es.md)

## Configurar un proyecto nuevo

### Manual

Desde la raíz de un proyecto nuevo:

```bash
cp /path/to/skills/AGENTS.md .
cp -R /path/to/skills/memory-bank .
cp -R /path/to/skills/evolution .
mkdir -p docs
```

Después edite los archivos copiados en este orden:

1. `memory-bank/product.md`: definir qué es y qué no es el proyecto.
2. `memory-bank/architecture.md`: definir layout, flujo de datos y límites.
3. `memory-bank/tech-stack.md`: definir comandos, dependencias y harnesses.
4. `memory-bank/milestone.md`: definir el primer milestone.
5. `memory-bank/status.md`: definir las primeras filas accionables.
6. `evolution/prompt-v1.md`: registrar la dirección inicial.
7. `evolution/result-v1.md`: registrar el estado inicial actual.
8. `AGENTS.md`: reemplazar placeholders con comandos y reglas específicos del proyecto.

Mantenga `README.md` simple y orientado al usuario. Ponga las referencias largas en `docs/`.

### Con ayuda de un agente de IA

Para un proyecto nuevo, puede usar los archivos de ejemplo como estructura inicial y pedir a un agente de IA que los complete después de describir el producto.

Advertencia: copiar estos archivos sobre un proyecto existente puede sobrescribir archivos que ya estén en disco. Haga una copia de seguridad o haga commit del trabajo actual primero.

Desde la raíz del proyecto nuevo:

```bash
cp /path/to/skills/AGENTS.md .
cp -R /path/to/skills/memory-bank .
cp -R /path/to/skills/evolution .
mkdir -p docs
```

Luego converse con el agente hasta que el producto, usuarios, límites, comandos y primer milestone estén claros. Pídale que complete:

- `AGENTS.md`
- `memory-bank/product.md`
- `memory-bank/architecture.md`
- `memory-bank/tech-stack.md`
- `memory-bank/milestone.md`
- `memory-bank/status.md`
- `evolution/prompt-v1.md`
- `evolution/result-v1.md`

Prompt de ejemplo:

```text
Read the sample AGENTS.md, memory-bank/*, and evolution/* files. Based on our
discussion of this new project, replace the placeholders with accurate project
content. Keep README user-facing, put long-form references in docs/, and make
memory-bank/status.md contain the first actionable milestone rows.
```

## Configurar un proyecto existente

### Manual

Para un proyecto existente, lea antes de escribir:

```bash
find . -name '*.md' -print | sort
rg -n "TODO|FIXME|roadmap|architecture|security|deploy|test|release" .
rg --files
```

Luego:

1. Lea el README raíz, guías de agentes, docs, README de paquetes y comentarios importantes de paquetes.
2. Copie `AGENTS.md`, `memory-bank/` y `evolution/` desde este repositorio.
3. Complete el memory bank desde lo que el proyecto ya dice, no desde una reescritura imaginada.
4. Mueva referencias largas y estables a `docs/`.
5. Convierta material duplicado de roadmap/status en `memory-bank/milestone.md` y `memory-bank/status.md`.
6. Mantenga las brechas conocidas visibles en `status.md` en vez de ocultarlas.

### Con ayuda de un agente de IA

Para un proyecto existente, el agente puede hacer el inventario y el primer borrador del memory bank. Funciona mejor cuando el proyecto ya tiene README, docs, comentarios de paquetes, pruebas o archivos CI útiles.

Advertencia: copiar estos archivos de ejemplo en un proyecto existente puede sobrescribir `AGENTS.md`, `memory-bank/` o `evolution/` existentes. Haga commit primero, cree una copia de seguridad o copie las muestras a una ubicación temporal antes de pedir al agente que las fusione.

Desde la raíz del proyecto existente:

```bash
cp /path/to/skills/AGENTS.md .
cp -R /path/to/skills/memory-bank .
cp -R /path/to/skills/evolution .
mkdir -p docs
```

Después pida al agente que lea el proyecto antes de escribir:

```text
Read the existing README, docs, package README files, tests, build files, and
major source directories. Use that actual project content to fill in AGENTS.md,
memory-bank/*, and evolution/*. Preserve useful existing documentation by moving
long-form references into docs/. Keep known gaps visible in memory-bank/status.md.
Do not invent product direction that is not supported by the existing project.
```

El agente debe:

1. Inventariar el markdown existente y el layout del código fuente.
2. Identificar comandos, dependencias, pruebas y harnesses.
3. Completar el memory bank desde la realidad actual del proyecto.
4. Mover o resumir referencias largas en `docs/`.
5. Mantener `README.md` simple y orientado al usuario.
6. Dejar brechas no resueltas como filas pending o blocked en `memory-bank/status.md`.

## Usar el Memory Bank

Con un agente como Codex o Claude Code, el flujo de trabajo visible para el usuario puede ser tan simple como escribir:

```text
tackle next pending item in memory bank
```

El agente debe encontrar la siguiente fila accionable en `memory-bank/status.md`, completar esa tarea, ejecutar la verificación requerida, actualizar el memory bank y hacer un git commit con alcance claro. Si esa fila es el último elemento abierto de un milestone, el agente debe ejecutar la revisión de milestone desde `memory-bank/milestone.md` antes de continuar. Durante esa revisión también debe decidir si `evolution/` necesita una nueva versión porque la dirección del producto, el límite de arquitectura, el objetivo del milestone o la dirección del contrato público/privado cambiaron materialmente.

Debajo de la superficie, el flujo normal del agente es:

1. Leer `AGENTS.md`.
2. Leer los archivos del memory bank en el orden indicado por `AGENTS.md`.
3. Abordar exactamente una tarea o fila de estado con alcance claro.
4. Actualizar el archivo memory-bank correspondiente si cambiaron scope, architecture, tools, milestone acceptance o status.
5. Marcar una fila como `[+]` solo después de que pase la verificación.
6. Hacer commit de la fila como una unidad con alcance claro.
7. Si un milestone queda completo, ejecutar el procedimiento de revisión de milestone en `memory-bank/milestone.md` antes de continuar.
8. Revisar `evolution/` y agregar una nueva versión solo cuando la revisión encuentre un cambio real de dirección, límite, milestone o contrato.

Las filas de estado usan estos marcadores:

| Símbolo | Significado |
|---|---|
| `[ ]` | Pendiente |
| `[+]` | Completado |
| `[~]` | En curso |
| `[!]` | Bloqueado |
| `[X]` | Cancelado |

## Instalar el API Harness

El API harness es a nivel de cuenta porque puede manejar cualquier proyecto que siga esta forma de memory-bank.

```bash
mkdir -p ~/.local/bin ~/.codex/prompts
cp /path/to/skills/.local/bin/tackle-memory-bank-api-loop ~/.local/bin/
cp /path/to/skills/.codex/prompts/tackle-next-memory-bank-todo.md ~/.codex/prompts/
chmod +x ~/.local/bin/tackle-memory-bank-api-loop
```

Ejecutar una fila:

```bash
LLM_MODEL=gpt-5.5 OPENAI_API_KEY=... MAX_RUNS=1 tackle-memory-bank-api-loop .
```

Ejecutar un bucle:

```bash
LLM_MODEL=gpt-5.5 OPENAI_API_KEY=... MAX_RUNS=5 tackle-memory-bank-api-loop .
```

Usar un proveedor compatible con OpenAI:

```bash
LLM_API_BASE=https://openrouter.ai/api/v1 \
LLM_API_KEY=... \
LLM_MODEL=openai/gpt-5.5 \
MAX_RUNS=1 \
tackle-memory-bank-api-loop .
```

Usar un servidor local compatible con OpenAI:

```bash
LLM_API_BASE=http://localhost:1234/v1 \
LLM_MODEL=local-model-name \
MAX_RUNS=1 \
tackle-memory-bank-api-loop .
```

El harness incrusta la instrucción de la tarea en su prompt API. No llama a Codex CLI y no requiere el archivo externo de prompt en tiempo de ejecución. El archivo de prompt se incluye como referencia reutilizable para personas y agentes.

## Qué es el harness

Para trabajo normal de proyecto, `tackle-memory-bank-api-loop` es un harness de ejecución: ejecuta repetidamente un agente contra un repositorio, le da acceso shell mediante un protocolo de comandos controlado y comprueba el estado git entre ejecuciones.

Se vuelve parte de un harness de evaluación de modelos solo cuando se puntúan resultados entre modelos, prompts, pass rates, review findings, cost, latency o regressions.

Leer más:

- [Harness de ejecución](docs/EXECUTION_es.md)
- [Harness de evaluación de modelos](docs/MODEL_EVAL_es.md)

## Reglas de mantenimiento

- Mantener `AGENTS.md` corto.
- Mantener el `README.md` del proyecto orientado al usuario.
- Poner explicaciones largas en `docs/`.
- Poner la verdad activa en `memory-bank/`.
- Poner snapshots históricos de dirección en `evolution/`.
- Actualizar memory en el mismo commit que el código o los docs que describe.
- Agregar una nueva versión de evolution solo ante un cambio real de dirección.
- Eliminar docs duplicadas una vez que el contenido útil se haya fusionado.
