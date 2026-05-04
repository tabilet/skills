# Modell-Evaluierungs-Harness

Ein Modell-Evaluierungs-Harness (model eval harness) ist die wiederholbare Art, modellgestütztes Verhalten zu messen. Er ist nützlich, wenn ein Projekt von Prompts, Agenten, Klassifikatoren, Retrieval, Ranking, Generierung, Code-Reparatur, Zusammenfassung oder einem anderen Workflow abhängt, bei dem Modellqualität zählt und normale Softwaretests nicht ausreichen.

Ein Ausführungs-Harness fragt: lief die Software korrekt?

Ein Modell-Evaluierungs-Harness fragt: wurde das Modellverhalten auf repräsentativen Aufgaben besser, schlechter oder blieb es gleich?

## Beispiele

- Ein Dataset aus Benutzeranfragen, erwarteten Antworten und Bewertungsrubriken.
- Eine Prompt-Regression-Suite, die alte und neue Prompts vergleicht.
- Ein Baseline-vs-Candidate-Lauf, der accuracy, pass rate, refusal quality, latency und cost misst.
- Ein Code-Repair-Eval, bei dem erzeugte Patches in Sandboxes gebaut und getestet werden.
- Ein Retrieval-Eval, das misst, ob die richtigen Dokumente ausgewählt wurden.
- Ein Report, der Regressionen, Verbesserungen und ungelöste Residuals auflistet.

## Wo er hineinpasst

- `memory-bank/product.md` beschreibt, welches modellgestützte Verhalten für das Produkt wichtig ist.
- `memory-bank/architecture.md` dokumentiert, wo Prompts, Datasets, Grader und Reports liegen.
- `memory-bank/tech-stack.md` dokumentiert Modellanbieter, lokale Runner, Eval-Befehle, Umgebungsvariablen, Kostenkontrollen und erforderliche Zugangsdaten.
- `memory-bank/milestone.md` kann einen Eval-Score oder einen Regression-Review als Teil der Akzeptanz definieren.
- `evolution/` hält größere Richtungsänderungen bei Prompt, Modell, Architektur oder Benchmark fest.

## Den API Loop zu einem Eval machen

Der enthaltene API loop ist nicht automatisch ein Modell-Evaluierungs-Harness. Er wird Teil eines solchen Harnesses, wenn kontrollierte Vergleiche ausgeführt und Ergebnisse festgehalten werden.

Nützliche Messwerte:

- Modellname,
- Prompt-Version,
- Dataset oder Todo-Set,
- pass/fail,
- Anzahl der Schleifeniterationen,
- Testergebnisse,
- Ergebnisse der statischen Analyse,
- Review-Ergebnisse,
- menschliche Akzeptanz,
- Kosten,
- Latenz,
- eingeführte Regressionen,
- verbleibende Fehler.

## Promotion-Regeln

Bevor ein neues Modell, ein neuer Prompt oder ein neuer Agenten-Workflow promoted wird, definieren Sie:

- Baseline-Modell und Prompt,
- Candidate-Modell und Prompt,
- Dataset oder Task-Set,
- primäre Metrik,
- erlaubtes Regression-Budget,
- erforderliche deterministische Checks,
- Anforderungen an menschlichen Review,
- Report-Speicherort.

Die Promotion-Regel sollte so eindeutig sein, dass ein Reviewer erklären kann, warum der Candidate bestanden hat oder gescheitert ist.

## Reports

Ein Eval-Report sollte aufführen:

- was ausgeführt wurde,
- was sich geändert hat,
- aggregierter Score,
- verbesserte Fälle,
- regredierte Fälle,
- flaky oder nicht eindeutige Fälle,
- Kosten und Latenz,
- ungelöste Residuals,
- Promotion-Entscheidung.

Speichern Sie Reports in der Nähe des Eval-Harnesses oder an einem dokumentierten Artifact-Ort, und verlinken Sie wichtige Richtungsänderungen aus `evolution/`.
