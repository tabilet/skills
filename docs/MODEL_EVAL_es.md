# Harness de evaluación de modelos

Un harness de evaluación de modelos (model eval harness) es la forma repetible de medir comportamiento asistido por modelos. Es útil cuando un proyecto depende de prompts, agentes, clasificadores, retrieval, ranking, generación, reparación de código, resumen o cualquier flujo de trabajo donde la calidad del modelo importa y las pruebas de software normales no bastan.

Un harness de ejecución pregunta: ¿el software se ejecutó correctamente?

Un harness de evaluación de modelos pregunta: ¿el comportamiento del modelo mejoró, empeoró o se mantuvo igual en tareas representativas?

## Ejemplos

- Un dataset de solicitudes de usuarios, respuestas esperadas y rúbricas de calificación.
- Una suite de regresión de prompts que compara prompts antiguos y nuevos.
- Una ejecución baseline-vs-candidate que mide accuracy, pass rate, refusal quality, latency y cost.
- Una code-repair eval donde los patches generados se compilan y prueban en sandboxes.
- Una retrieval eval que mide si se seleccionaron los documentos correctos.
- Un informe que enumera regresiones, mejoras y residuales no resueltos.

## Dónde encaja

- `memory-bank/product.md` dice qué comportamiento asistido por modelos importa para el producto.
- `memory-bank/architecture.md` registra dónde viven prompts, datasets, graders e informes.
- `memory-bank/tech-stack.md` registra proveedores de modelos, runners locales, comandos de eval, variables de entorno, controles de costo y credenciales necesarias.
- `memory-bank/milestone.md` puede hacer que una puntuación de eval o una revisión de regresión sea parte de la aceptación.
- `evolution/` registra cambios importantes de dirección en prompt, modelo, arquitectura o benchmark.

## Convertir el API Loop en una eval

El API loop incluido no es automáticamente un harness de evaluación de modelos. Se vuelve parte de uno cuando se ejecutan comparaciones controladas y se registran los resultados.

Mediciones útiles:

- nombre del modelo,
- versión del prompt,
- dataset o todo set,
- pass/fail,
- número de iteraciones del bucle,
- resultados de pruebas,
- resultados de análisis estático,
- hallazgos de review,
- aceptación humana,
- costo,
- latencia,
- regresiones introducidas,
- fallos residuales.

## Reglas de promoción

Antes de promover un nuevo modelo, prompt o flujo de trabajo de agentes, defina:

- modelo y prompt baseline,
- modelo y prompt candidate,
- dataset o task set,
- métrica principal,
- presupuesto de regresión permitido,
- checks deterministas requeridos,
- requisitos de review humano,
- ubicación del informe.

La regla de promoción debe ser lo bastante explícita para que un reviewer pueda decir por qué el candidate pasó o falló.

## Informes

Un informe de eval debe enumerar:

- qué se ejecutó,
- qué cambió,
- puntuación agregada,
- casos mejorados,
- casos con regresión,
- casos flaky o inconclusos,
- costo y latencia,
- residuales no resueltos,
- decisión de promoción.

Guarde los informes cerca del harness de eval o en una ubicación documentada de artifacts, y enlace los cambios de dirección importantes desde `evolution/`.
