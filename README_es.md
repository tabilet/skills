# Un harness mínimo de ingeniería

Los agentes de código trabajan mejor cuando un proyecto sabe explicarse: qué es, qué está hecho, qué viene después. La forma habitual de conseguirlo es adoptar un sistema: un CLI, un scaffold, un conjunto de comandos slash, una carpeta de artefactos generados. Seis meses después mantiene los archivos de ese sistema tanto como su propio código, y su proyecto vive dentro de las convenciones de ese sistema en lugar de las suyas.

Este repositorio apuesta por lo contrario. Cinco o seis archivos markdown, copiados a su proyecto, suyos por completo. Ningún CLI que instalar, ningún vocabulario que aprender, nada obligatorio. Borre cualquiera de ellos el día en que deje de merecer su sitio.

**Aquí no se ejecuta nada.** Este repositorio es un punto de partida del que se copia *hacia fuera*: `template/` a su proyecto y `harness/` opcionalmente a su directorio personal. Después su proyecto no depende de este repositorio ni mantiene enlace de vuelta. Ese es justamente el objetivo: lo que le queda es suyo.

Su proyecto acaba con este aspecto:

```text
your-project/
├── AGENTS.md              lo que un agente debe leer primero
├── memory-bank/           lo que es cierto ahora
│   ├── product.md         qué es y qué no es
│   ├── architecture.md    estructura, flujo de datos, fronteras
│   ├── tech-stack.md      comandos, dependencias, verificación
│   ├── milestone.md       milestones y criterios de aceptación
│   └── status-M01.md      un archivo por milestone, una fila por tarea
└── evolution/             por qué cambió la dirección
```

A lo largo del documento, **harness** significa un comando repetible que demuestra que algo funciona: su suite de pruebas, un job de CI, un script. Su proyecto define el suyo en `tech-stack.md`. Este repositorio incluye además un harness opcional: un bucle por API que conduce a un agente a través del memory bank sin supervisión.

Otras versiones de idioma: [🇬🇧 English](README.md) · [🇨🇳 中文](README_cn.md) · [🇯🇵 日本語](README_ja.md) · [🇩🇪 Deutsch](README_de.md) · [🇫🇷 Français](README_fr.md).

## Primeros pasos

**Para usar el memory bank necesita `git`, y nada más.** El memory bank es markdown corriente, así que el flujo diario —pedirle a un agente como Codex o Claude Code que atienda el siguiente pendiente— no necesita ningún runtime.

**Python 3 solo hace falta para el harness API opcional**, el bucle desatendido que describe [Instalar el API Harness](#instalar-el-api-harness). Usa solo la biblioteca estándar, así que no hay nada que instalar con `pip`. Omítalo por completo si ya maneja el memory bank desde un agente que usa habitualmente.

Las instrucciones para proyectos existentes, más abajo, también usan [ripgrep](https://github.com/BurntSushi/ripgrep) (`rg`) para el inventario inicial.

Clone este repositorio una vez. Cada comando `cp` de abajo se refiere a su clon como `/path/to/skills`:

```bash
git clone https://github.com/tabilet/skills.git
cd skills
```

Nada se ejecuta desde el clon en sí. Usted copia archivos hacia fuera: `template/` a un proyecto y `harness/` a su directorio personal.

## Qué hay en este repositorio

Archivos de ejemplo a nivel de proyecto:

- [template/AGENTS.md](template/AGENTS.md)
- [template/GOAL.md](template/GOAL.md) — el protocolo de ejecución multi-milestone
- [template/memory-bank/product.md](template/memory-bank/product.md)
- [template/memory-bank/architecture.md](template/memory-bank/architecture.md)
- [template/memory-bank/tech-stack.md](template/memory-bank/tech-stack.md)
- [template/memory-bank/milestone.md](template/memory-bank/milestone.md)
- [template/memory-bank/status-M01.md](template/memory-bank/status-M01.md)
- [template/evolution/prompt-v1.md](template/evolution/prompt-v1.md)
- [template/evolution/result-v1.md](template/evolution/result-v1.md)

Archivos de ejemplo a nivel de cuenta de usuario:

- [harness/tackle-memory-bank-api-loop](harness/tackle-memory-bank-api-loop)
- [harness/prompts/tackle-next-memory-bank-todo.md](harness/prompts/tackle-next-memory-bank-todo.md)

Referencias de harness:

- [Harness de ejecución](docs/EXECUTION_es.md)
- [Harness de evaluación de modelos](docs/MODEL_EVAL_es.md)

## Cómo se ve un memory bank completado

La plantilla trae placeholders. Este es el mismo memory bank completado para un pequeño servicio de tienda, para ver el destino antes que las indicaciones.

`memory-bank/product.md` empieza como `[project-name] is [one or two sentences describing the project]` y queda así:

```markdown
`cartsvc` is the shopping cart and checkout service behind the storefront.
It owns cart state, pricing, and the handoff to payments.
```

`memory-bank/milestone.md` decide cómo se organiza todo lo demás: nombra los carriles y dice qué cubre cada uno.

```markdown
## Status ID Pattern

M01, M02, ...   Default lane: cross-cutting work, infrastructure, chores
S01, S02, ...   Storefront: cart, checkout, product pages
A01, A02, ...   Accounting: pricing, invoices, payment reconciliation

Lane meanings:

- `M`: anything that does not belong to a product domain.
- `S`: shopping surface. Owned by the storefront team.
- `A`: money. Changes here need a second reviewer.

## Status Files

| Milestone | Status File | Summary |
|---|---|---|
| S01 | [status-S01.md](status-S01.md) | Cart and checkout. |
| A02 | [status-A02.md](status-A02.md) | Payment contract. |

## S01 - Cart And Checkout

**Goal.** A shopper can fill a cart and complete a purchase.

**Scope.**

- Cart CRUD behind `POST /cart`.
- Line-item and order-total pricing.
- Handoff to the payment provider.

**Acceptance.** `make test` passes, and a scripted end-to-end purchase
succeeds against the staging payment sandbox.
```

Después `memory-bank/status-S01.md` lleva las filas de ese milestone:

```markdown
# Status S01 - Cart And Checkout

| Item | State | Notes |
|---|---|---|
| Add POST /cart endpoint | `[+]` | Verified by tests/cart_test.py. |
| Cart total calculation | `[~]` | Rounding rules still open. |
| Wire cart to checkout | `[ ]` | Blocked on the A02 payment contract. |
| Guest checkout | `[X]` | Cancelled; accounts required at launch. |
```

**Los backticks alrededor de cada marcador son obligatorios.** El harness coincide con `` `[ ]` ``, no con `[ ]`. Una fila escrita `| Item | [ ] | Notes |` se ignora en silencio: el harness informa «No actionable memory-bank rows remain» y termina correctamente, como si el trabajo estuviera hecho.

## Configurar un proyecto nuevo

### Manual

Desde la raíz de un proyecto nuevo:

```bash
cp -R /path/to/skills/template/. .
mkdir -p docs
```

Después edite los archivos copiados en este orden:

1. `memory-bank/product.md`: definir qué es y qué no es el proyecto.
2. `memory-bank/architecture.md`: definir layout, flujo de datos y límites.
3. `memory-bank/tech-stack.md`: definir comandos, dependencias y harnesses.
4. `memory-bank/milestone.md`: definir el primer milestone.
5. `memory-bank/status-M01.md`: definir las primeras filas accionables. Vea más abajo «Cómo se ve un archivo de estado completado»: los backticks de los marcadores son decisivos.
6. `evolution/prompt-v1.md`: registrar la dirección inicial.
7. `evolution/result-v1.md`: registrar el estado inicial actual.
8. `AGENTS.md`: reemplazar placeholders con comandos y reglas específicos del proyecto.

Mantenga `README.md` simple y orientado al usuario. Ponga las referencias largas en `docs/`.

### Conectar su agente

`AGENTS.md` es un [estándar abierto entre proveedores](https://agents.md) mantenido por la Agentic AI Foundation. La mayoría de los agentes de código lo leen sin ninguna configuración: Codex, Cursor, Gemini CLI, GitHub Copilot, Devin, Windsurf, Jules, Junie, Zed, Aider, VS Code, Warp, goose, opencode, Amp, entre otros.

En `template/` no se incluye ningún archivo específico de un proveedor. Si su agente lee otro nombre de archivo, enlácelo a `AGENTS.md` en una línea en vez de mantener una segunda copia que se desviará:

| Agente | Puente |
|---|---|
| Cualquiera de la lista anterior | Nada que hacer |
| Claude Code | `ln -s AGENTS.md CLAUDE.md`, o un `CLAUDE.md` con `@AGENTS.md` |
| Otras herramientas con archivo propio | Symlink o import apuntando a `AGENTS.md`, igual |

En Windows los symlinks requieren Administrador o Modo de desarrollador, así que allí conviene la forma import.

### Con ayuda de un agente de IA

Para un proyecto nuevo, puede usar los archivos de ejemplo como estructura inicial y pedir a un agente de IA que los complete después de describir el producto.

Advertencia: copiar estos archivos sobre un proyecto existente puede sobrescribir archivos que ya estén en disco. Haga una copia de seguridad o haga commit del trabajo actual primero.

Desde la raíz del proyecto nuevo:

```bash
cp -R /path/to/skills/template/. .
mkdir -p docs
```

Luego converse con el agente hasta que el producto, usuarios, límites, comandos y primer milestone estén claros. Pídale que complete:

- `AGENTS.md`
- `memory-bank/product.md`
- `memory-bank/architecture.md`
- `memory-bank/tech-stack.md`
- `memory-bank/milestone.md`
- `memory-bank/status-M01.md`
- `evolution/prompt-v1.md`
- `evolution/result-v1.md`

Prompt de ejemplo:

```text
Read the sample AGENTS.md, memory-bank/*, and evolution/* files. Based on our
discussion of this new project, replace the placeholders with accurate project
content. Keep README user-facing, put long-form references in docs/, define the status
ID lanes in memory-bank/milestone.md, and make memory-bank/status-M01.md contain
the first actionable milestone rows.
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
2. Copie `template/` desde este repositorio.
3. Complete el memory bank desde lo que el proyecto ya dice, no desde una reescritura imaginada.
4. Mueva referencias largas y estables a `docs/`.
5. Convierta material duplicado de roadmap/status en `memory-bank/milestone.md` y `memory-bank/status-<LANE><NN>.md`.
6. Mantenga las brechas conocidas visibles en `status-<LANE><NN>.md` en vez de ocultarlas.

### Con ayuda de un agente de IA

Para un proyecto existente, el agente puede hacer el inventario y el primer borrador del memory bank. Funciona mejor cuando el proyecto ya tiene README, docs, comentarios de paquetes, pruebas o archivos CI útiles.

Advertencia: copiar estos archivos de ejemplo en un proyecto existente puede sobrescribir `AGENTS.md`, `memory-bank/` o `evolution/` existentes. Haga commit primero, cree una copia de seguridad o copie las muestras a una ubicación temporal antes de pedir al agente que las fusione.

Desde la raíz del proyecto existente:

```bash
cp -R /path/to/skills/template/. .
mkdir -p docs
```

Después pida al agente que lea el proyecto antes de escribir:

```text
Read the existing README, docs, package README files, tests, build files, and
major source directories. Use that actual project content to fill in AGENTS.md,
memory-bank/*, and evolution/*. Preserve useful existing documentation by moving
long-form references into docs/. Keep known gaps visible in the matching
memory-bank/status-<LANE><NN>.md file.
Do not invent product direction that is not supported by the existing project.
```

El agente debe:

1. Inventariar el markdown existente y el layout del código fuente.
2. Identificar comandos, dependencias, pruebas y harnesses.
3. Completar el memory bank desde la realidad actual del proyecto.
4. Mover o resumir referencias largas en `docs/`.
5. Mantener `README.md` simple y orientado al usuario.
6. Dejar brechas no resueltas como filas pending o blocked en `memory-bank/status-<LANE><NN>.md`.

## Usar el Memory Bank

Hay tres formas de ejecutar trabajo sobre el memory bank, y todas son opcionales: el memory bank es markdown corriente y funciona por sí solo:

| Forma de ejecutar | Alcance | Necesita |
|---|---|---|
| Escribirle una petición a su agente | Una fila cada vez, con usted en el bucle | Nada |
| [El harness API](#instalar-el-api-harness) | Una fila por ejecución, desatendido | Python 3 |
| [Un bucle de goal](#ejecutar-varios-milestones-en-orden) | Varios milestones en orden | Un comando `/goal` |

Con un agente como Codex o Claude Code, el flujo de trabajo visible para el usuario puede ser tan simple como escribir:

```text
tackle next pending item in memory bank
```

El agente debe encontrar la siguiente fila accionable en `memory-bank/status-<LANE><NN>.md`, completar esa tarea, ejecutar la verificación requerida, actualizar el memory bank y hacer un git commit con alcance claro. Si esa fila es el último elemento abierto de un milestone, el agente debe ejecutar la revisión de milestone desde `memory-bank/milestone.md` antes de continuar. Durante esa revisión también debe decidir si `evolution/` necesita una nueva versión porque la dirección del producto, el límite de arquitectura, el objetivo del milestone o la dirección del contrato público/privado cambiaron materialmente.

Antes de confiar en todo esto, dele al agente algo contra lo que verificar. Rellene la tabla **Execution harnesses** de `memory-bank/tech-stack.md` con el comando que demuestra que su proyecto funciona —`make test`, `npm test`, un script, lo que ya ejecute— y qué demuestra que pase. Una fila no debería llegar a `[+]` hasta que ese comando haya pasado. Sin eso, «marcar una fila completa solo tras verificar» no tiene referente y el agente decide por su cuenta qué significa verificado.

Debajo de la superficie, el flujo normal del agente es:

1. Leer `AGENTS.md`.
2. Leer los archivos del memory bank en el orden indicado por `AGENTS.md`.
3. Abordar exactamente una tarea o fila de estado con alcance claro.
4. Actualizar el archivo memory-bank correspondiente si cambiaron scope, architecture, tools, milestone acceptance o status.
5. Marcar una fila como `[+]` solo después de que pase la verificación.
6. Hacer commit de la fila como una unidad con alcance claro.
7. Si un milestone queda completo, ejecutar el procedimiento de revisión de milestone en `memory-bank/milestone.md` antes de continuar.
8. Revisar `evolution/` y agregar una nueva versión solo cuando la revisión encuentre un cambio real de dirección, límite, milestone o contrato.

### Carriles de ID de estado

Los archivos de estado se llaman `memory-bank/status-<LANE><NN>.md`. La letra de carril clasifica el trabajo y el número lleva dos dígitos con cero a la izquierda: los milestones de contabilidad quedan como `status-A01.md` y `status-A02.md`, y los de compras como `status-S01.md`. `M` es el carril por defecto para el trabajo que no encaja en un carril de dominio. Un carril admite como máximo 99 archivos; cuando se llena, abra una letra nueva en vez de añadir un tercer dígito. `memory-bank/milestone.md` registra qué significa cada letra y evita reutilizar un identificador.

**Cómo elegir carriles.** Un carril es una vía de trabajo de larga vida, no un milestone ni un sprint. Clasifique por dominio —la parte del producto a la que pertenece un cambio— y no por equipo, prioridad o fecha, porque los dominios sobreviven a los tres. Empiece solo con `M`; separe una letra la primera vez que un dominio tenga tanto trabajo que sus filas ahoguen al resto, o cuando necesite su propia cadencia de revisión. Dos o tres carriles es un estado estable normal, y un proyecto puede funcionar mucho tiempo con uno.

Quedarse corto se arregla barato: abra una letra nueva y ponga allí el trabajo nuevo. Pasarse no, porque los identificadores no se reutilizan ni se renombran una vez que existe su archivo: un carril del que se arrepienta se queda en el árbol para siempre. Ante la duda, déjelo en `M`.

Las filas de estado usan estos marcadores:

| Símbolo | Significado |
|---|---|
| `[ ]` | Pendiente |
| `[+]` | Completado |
| `[~]` | En curso |
| `[!]` | Bloqueado |
| `[X]` | Cancelado |

### Ejecutar varios milestones en orden

El flujo anterior avanza una fila cada vez. Para recorrer varios milestones en un orden definido, [GOAL.md](template/GOAL.md) es un protocolo posible para eso: concilia las dependencias antes de cada milestone, concilia los milestones posteriores al que acaba de cerrarse y se detiene en vez de adivinar cuando falta una decisión o una autorización.

Se invoca, no está siempre activo. Codex y Claude Code ofrecen un comando `/goal` —el de Claude Code sigue trabajando entre turnos hasta que se cumple la condición del goal— y la petición nombra el archivo y el orden:

Se invoca, no está siempre activo. Sea cual sea tu agente, la petición que inicia una ejecución es el mismo bloque: nombra el archivo, el orden y la política de commits:

```text
Using GOAL.md, execute this loop.

STATUS_ORDER: M01 -> S01 -> A01?
COMMIT_POLICY: task
```

Cómo envías ese bloque cambia, porque `/goal` no es el mismo comando en todos los agentes. Usa la sección del tuyo.

#### Si usas Claude Code

`/goal` está integrado y **no** es una forma de iniciar una tarea. Define una condición de parada —«un objetivo que Claude comprueba antes de detenerse»—, de modo que la sesión sigue trabajando a lo largo de varios turnos en vez de terminar tras una respuesta.

Por eso hacen falta dos mensajes. Envía el bloque anterior como un mensaje normal y luego define la condición que decide cuándo termina la ejecución:

```text
/goal every row in M01 and S01 is `[+]` and the required verification passes
```

`/goal active` muestra la condición actual y `/goal clear` la termina antes de tiempo. La condición está limitada a 4000 caracteres, necesita un espacio de trabajo de confianza y no está disponible cuando los hooks están desactivados por configuración o por política.

Para que el bloque en sí sea reutilizable, guárdalo como comando de proyecto, pero no como `.claude/commands/goal.md`, porque ese nombre lo ocupa el comando integrado. Llámalo `.claude/commands/milestones.md` e invócalo con `/milestones`.

#### Si usas Codex

No hay un `/goal` integrado. Los prompts personalizados son archivos markdown en `~/.codex/prompts/`, invocados por su nombre de archivo, así que puedes crear el comando tú mismo y hacer que reciba el orden como argumento. Crea `~/.codex/prompts/goal.md`:

```markdown
---
description: Execute an ordered set of milestones using GOAL.md.
argument-hint: M01 -> S01 -> A01?
---

Using GOAL.md, execute this loop.

STATUS_ORDER: $ARGUMENTS
COMMIT_POLICY: task
```

Entonces un solo mensaje lo ejecuta:

```text
/goal M01 -> S01 -> A01?
```

Es el mismo mecanismo que el prompt [tackle-next-memory-bank-todo.md](harness/prompts/tackle-next-memory-bank-todo.md) incluido, que se instala en el mismo directorio.

#### Cualquier otro agente

Pega el bloque como una petición normal. Al protocolo solo le hace falta que se nombre el archivo; nada depende de que exista un comando slash.

`COMMIT_POLICY` importa, y un bucle de goal es una excepción deliberada a la regla habitual. Durante esa ejecución es toda la regla de commits: `AGENTS.md` puede decir que cada fila de estado es una unidad de commit, pero `COMMIT_POLICY: none` —el valor por defecto del protocolo— significa ningún commit en absoluto, y eso es el comportamiento correcto, no un conflicto. Escriba `task` cuando quiera los commits por fila de siempre. La precedencia es la petición, luego `GOAL.md`, luego `AGENTS.md`, y solo para los commits, y solo dentro de la ejecución.

Una `?` final marca un milestone como condicional: se omite, no se cancela, cuando falta su disparador documentado.

`GOAL.md` no lleva rutas, letras de carril ni comandos propios de un proyecto. Los lee de `AGENTS.md` y del memory bank, así que el mismo archivo sirve sin cambios en cualquier proyecto que lo copie.

Nada le obliga a usarlo. `/goal` es el comando de su agente, no de este harness: traiga su propio protocolo, o ninguno, y el memory bank se comporta igual. `GOAL.md` se incluye porque escribir uno de estos es engorroso, no porque algo de aquí dependa de él. Si tiene el suyo, apunte a él las dos menciones de `GOAL.md` —en `AGENTS.md` y `memory-bank/milestone.md`— o bórrelas.

## Instalar el API Harness

Esta sección es opcional. Todo lo anterior funciona sin ella: el harness solo añade un bucle desatendido que maneja un agente por la API en vez de que usted escriba. Omítala si Codex, Claude Code u otro agente ya hace eso por usted.

El API harness es a nivel de cuenta porque puede manejar cualquier proyecto que siga esta forma de memory-bank. Necesita Python 3 y nada más.

```bash
mkdir -p ~/.local/bin ~/.codex/prompts
cp /path/to/skills/harness/tackle-memory-bank-api-loop ~/.local/bin/
cp /path/to/skills/harness/prompts/tackle-next-memory-bank-todo.md ~/.codex/prompts/
chmod +x ~/.local/bin/tackle-memory-bank-api-loop
```

Los comandos de abajo llaman a `tackle-memory-bank-api-loop` por su nombre, lo que requiere que `~/.local/bin` esté en su `PATH`. Si `command -v tackle-memory-bank-api-loop` no imprime nada, añada esta línea a su perfil de shell:

```bash
export PATH="$HOME/.local/bin:$PATH"
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

Usar Anthropic (Claude) en lugar de la ruta compatible con OpenAI:

```bash
LLM_PROVIDER=anthropic \
LLM_MODEL=claude-opus-5 \
ANTHROPIC_API_KEY=... \
MAX_RUNS=1 \
tackle-memory-bank-api-loop .
```

El harness incrusta la instrucción de la tarea en su prompt API. No llama a Codex CLI y no requiere el archivo externo de prompt en tiempo de ejecución. El archivo de prompt se incluye como referencia reutilizable para personas y agentes.

### Primera ejecución

Una ejecución imprime primero el repositorio, el proveedor, el modelo y el endpoint de la API, y luego trabaja una fila:

```text
Repo: /path/to/your-project
Provider: anthropic
Model: claude-opus-5
API: https://api.anthropic.com/v1/messages
Run 1/1: asking LLM to tackle one row.
  LLM turn 1/60
  shell: sed -n '1,120p' AGENTS.md  # Read the bootstrap guide.
```

El harness se detiene pronto a propósito, y su código de salida dice por qué. Del `3` al `7` son condiciones de parada normales, no fallos: `4` significa que el worktree no estaba limpio antes de la ejecución, y `6` que el agente terminó sin hacer commit. `11` significa que no encontró archivos `status-<LANE><NN>.md`, lo que suele indicar que el memory bank aún no se ha completado. La tabla completa está en [Harness de ejecución](docs/EXECUTION_es.md#códigos-de-salida).

## Qué es el harness

Para trabajo normal de proyecto, `tackle-memory-bank-api-loop` es un harness de ejecución: ejecuta repetidamente un agente contra un repositorio, le da acceso shell mediante un protocolo de comandos controlado y comprueba el estado git entre ejecuciones.

Descubre cada archivo `memory-bank/status-<LANE><NN>.md`, informa cuántas filas accionables y bloqueadas tiene cada carril, y deja que el agente elija la siguiente fila según el significado de los carriles y la prioridad de los milestones. Una fila bloqueada en un carril no detiene el trabajo en los demás; el bucle solo se detiene para revisión humana cuando ya solo quedan filas bloqueadas.

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
