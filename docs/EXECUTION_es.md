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
- `memory-bank/status.md` registra si las filas relacionadas con el harness están pending, complete, blocked o cancelled.

## Harness de ejecución de agentes

El archivo incluido [.local/bin/tackle-memory-bank-api-loop](../.local/bin/tackle-memory-bank-api-loop) es un harness de ejecución de agentes.

Hace lo siguiente:

- llama a una API chat-completions compatible con OpenAI,
- incrusta la instrucción de tarea de memory-bank directamente en la llamada API,
- le da al modelo un protocolo de comandos shell,
- se detiene cuando no quedan filas accionables,
- se detiene cuando existen filas blocked,
- comprueba que el git worktree esté limpio antes de cada ejecución,
- exige que el modelo haga commit de su trabajo,
- se detiene si el modelo deja cambios sin commit,
- se detiene si el modelo no crea ningún commit,
- limita el número de iteraciones del bucle.

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
