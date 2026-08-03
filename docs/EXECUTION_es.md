# Harness de ejecución

Un harness de ejecución (execution harness) es la forma repetible de ejecutar un proyecto bajo las condiciones que importan. Normalmente es un programa, script, objetivo de prueba, archivo Docker Compose o CI job.

Markdown no ejecuta el harness. Markdown explica a las personas y a los agentes cómo ejecutarlo, qué servicios inicia, qué evidencia produce y qué fallos son conocidos o esperados.

## Ejemplos

- Un objetivo `make test` que ejecuta todas las pruebas unitarias.
- Un objetivo `make integration` que inicia contenedores PostgreSQL y MySQL, ejecuta pruebas de base de datos y luego detiene los contenedores.
- Un paquete de pruebas Go que usa `testcontainers-go` para lanzar servicios reales.
- Un script que compila una CLI, la ejecuta contra entradas fixture y compara la salida generada con diff.
- Un CI workflow que ejecuta los mismos comandos en cada pull request.

## Dónde encaja

- `AGENTS.md` enumera los comandos harness esenciales que los agentes deben ejecutar.
- `memory-bank/tech-stack.md` registra prerrequisitos, variables de entorno, Docker images, puertos y nombres de comandos.
- `docs/` contiene notas extensas de setup, teardown y troubleshooting.
- `memory-bank/milestone.md` puede hacer que pasar un harness sea parte de la aceptación.
- `memory-bank/status-<LANE><NN>.md` registra si las filas relacionadas con el harness están pending, complete, blocked o cancelled.

## Harness de ejecución de agentes

El archivo incluido [harness/tackle-memory-bank-api-loop](../harness/tackle-memory-bank-api-loop) es un harness de ejecución de agentes.

Hace lo siguiente:

- llama a una API chat-completions compatible con OpenAI, o a la API Anthropic Messages con `LLM_PROVIDER=anthropic`,
- incrusta la instrucción de tarea de memory-bank directamente en la llamada API,
- le da al modelo un protocolo de comandos shell,
- descubre cada archivo de carril `memory-bank/status-<LANE><NN>.md` e informa al modelo cuántas filas accionables y bloqueadas tiene cada carril,
- se detiene cuando ningún carril conserva filas accionables,
- avisa de las filas blocked y solo se detiene para revisión humana cuando ya solo quedan filas blocked,
- comprueba que el git worktree esté limpio antes de cada ejecución,
- exige que el modelo haga commit de su trabajo,
- se detiene si el modelo deja cambios sin commit,
- se detiene si el modelo no crea ningún commit,
- limita el número de iteraciones del bucle.

### Códigos de salida

El harness señala cada resultado con su código de salida. Los códigos `3` a `7` son condiciones de parada normales, no fallos: el bucle devolvió el control a una persona a propósito.

| Código | Significado |
|---|---|
| `0` | No quedan filas accionables. Nada que hacer. |
| `2` | `LLM_MODEL` no está definido, o `LLM_PROVIDER` no es `openai` ni `anthropic`. |
| `3` | Solo quedan filas bloqueadas. Una persona debe desbloquearlas. |
| `4` | El worktree no estaba limpio antes de la ejecución. Haga commit o stash primero. |
| `5` | El agente dejó cambios sin commit. |
| `6` | El agente no creó ningún commit. Evita un bucle sin progreso. |
| `7` | Se alcanzó `MAX_RUNS`. |
| `10` | No hay `AGENTS.md` en el repositorio de destino. |
| `11` | No hay `memory-bank/`, o no contiene archivos `status-<LANE><NN>.md`. |
| `12` | La ruta de destino no está dentro de un worktree de git. |
| `13` | No se pudo leer el `HEAD` de git. |
| `20` | La API devolvió un error HTTP. |
| `21` | No se pudo contactar con la API. |
| `22` | La respuesta de la API no tenía la forma esperada. |
| `30` | El modelo agotó `MAX_TURNS` sin terminar una fila. |

Los códigos `10` a `13` significan que el repositorio de destino aún no está preparado. Los `20` a `22` son problemas del proveedor o de red, no del proyecto.

## Servicios respaldados por Docker

Para pruebas que necesitan servicios como MySQL o PostgreSQL, prefiera contenedores desechables en vez de instalaciones locales obligatorias.

Flujo típico:

1. Iniciar contenedores de servicio con Docker Compose, `testcontainers` o un script harness.
2. Esperar a que pasen los health checks.
3. Ejecutar las pruebas de integración.
4. Recopilar logs en caso de fallo.
5. Detener y eliminar los contenedores.

Esto mantiene más parecidos los equipos locales de desarrollo y los entornos CI.

## Documentar un harness

Para cada harness de ejecución, registre:

- comando,
- escenario,
- servicios requeridos,
- variables de entorno,
- fixture o seed data,
- salida esperada al pasar,
- ubicaciones de artifacts y logs,
- nombre del CI job,
- limitaciones conocidas o filas blocked.

La lista activa de comandos pertenece a `memory-bank/tech-stack.md`. Los detalles operativos más largos pertenecen a `docs/`.
