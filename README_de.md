# Ein minimaler Engineering-Harness

Dieses Repository ist ein kopierbarer Ausgangspunkt für ein leichtgewichtiges Projekt-Betriebssystem, aufgebaut um:

- `AGENTS.md` als Bootstrap-Leitfaden für Agenten.
- `memory-bank/` als aktuelle Source of Truth des Projekts.
- `evolution/` als versionierte Historie für Richtungsänderungen.
- Ausführungs-Harnesses als wiederholbare Befehle, die beweisen, dass die Software funktioniert.
- Modell-Evaluierungs-Harnesses als wiederholbare Evaluierungen, die modellgestütztes Verhalten messen.

Ziel ist nicht mehr Dokumentationsvolumen. Ziel ist ein kompaktes Betriebshandbuch, das Menschen und Agenten gemeinsam nutzen, und das anschließend mit ausführbaren Harnesses verbunden wird.

## Inhalt dieses Repositorys

Projektweite Beispieldateien:

- [AGENTS.md](AGENTS.md)
- [memory-bank/product.md](memory-bank/product.md)
- [memory-bank/architecture.md](memory-bank/architecture.md)
- [memory-bank/tech-stack.md](memory-bank/tech-stack.md)
- [memory-bank/milestone.md](memory-bank/milestone.md)
- [memory-bank/status.md](memory-bank/status.md)
- [evolution/prompt-v1.md](evolution/prompt-v1.md)
- [evolution/result-v1.md](evolution/result-v1.md)

Beispieldateien auf Benutzerkonto-Ebene:

- [.local/bin/tackle-memory-bank-api-loop](.local/bin/tackle-memory-bank-api-loop)
- [.codex/prompts/tackle-next-memory-bank-todo.md](.codex/prompts/tackle-next-memory-bank-todo.md)

Harness-Referenzen:

- [Ausführungs-Harness](docs/EXECUTION_de.md)
- [Modell-Evaluierungs-Harness](docs/MODEL_EVAL_de.md)

## Ein neues Projekt einrichten

### Manuell

Vom Root eines neuen Projekts aus:

```bash
cp /path/to/skills/AGENTS.md .
cp -R /path/to/skills/memory-bank .
cp -R /path/to/skills/evolution .
mkdir -p docs
```

Bearbeiten Sie die kopierten Dateien anschließend in dieser Reihenfolge:

1. `memory-bank/product.md`: definieren, was das Projekt ist und was nicht.
2. `memory-bank/architecture.md`: Layout, Datenfluss und Grenzen definieren.
3. `memory-bank/tech-stack.md`: Befehle, Abhängigkeiten und Harnesses definieren.
4. `memory-bank/milestone.md`: den ersten Milestone definieren.
5. `memory-bank/status.md`: die ersten ausführbaren Zeilen definieren.
6. `evolution/prompt-v1.md`: die Anfangsrichtung festhalten.
7. `evolution/result-v1.md`: den aktuellen Startzustand festhalten.
8. `AGENTS.md`: Platzhalter durch projektspezifische Befehle und Regeln ersetzen.

Halten Sie `README.md` einfach und benutzerorientiert. Längere Referenzen gehören in `docs/`.

### Mit Hilfe eines KI-Agenten

Für ein neues Projekt können Sie die Beispieldateien als Anfangsstruktur verwenden und einen KI-Agenten bitten, sie auszufüllen, nachdem Sie das Produkt beschrieben haben.

Warnung: Das Kopieren dieser Dateien über ein bestehendes Projekt kann vorhandene Dateien auf der Festplatte überschreiben. Erstellen Sie zuerst ein Backup oder committen Sie die aktuelle Arbeit.

Vom Root des neuen Projekts aus:

```bash
cp /path/to/skills/AGENTS.md .
cp -R /path/to/skills/memory-bank .
cp -R /path/to/skills/evolution .
mkdir -p docs
```

Sprechen Sie dann mit dem Agenten, bis Produkt, Benutzer, Grenzen, Befehle und erster Milestone klar sind. Bitten Sie ihn, Folgendes auszufüllen:

- `AGENTS.md`
- `memory-bank/product.md`
- `memory-bank/architecture.md`
- `memory-bank/tech-stack.md`
- `memory-bank/milestone.md`
- `memory-bank/status.md`
- `evolution/prompt-v1.md`
- `evolution/result-v1.md`

Beispiel-Prompt:

```text
Read the sample AGENTS.md, memory-bank/*, and evolution/* files. Based on our
discussion of this new project, replace the placeholders with accurate project
content. Keep README user-facing, put long-form references in docs/, and make
memory-bank/status.md contain the first actionable milestone rows.
```

## Ein bestehendes Projekt einrichten

### Manuell

Bei einem bestehenden Projekt erst lesen, dann schreiben:

```bash
find . -name '*.md' -print | sort
rg -n "TODO|FIXME|roadmap|architecture|security|deploy|test|release" .
rg --files
```

Dann:

1. Root-README, Agentenleitfäden, docs, Package-READMEs und wichtige Package-Kommentare lesen.
2. `AGENTS.md`, `memory-bank/` und `evolution/` aus diesem Repository kopieren.
3. Die Memory Bank aus dem füllen, was das Projekt bereits sagt, nicht aus einer ausgedachten Neuausrichtung.
4. Stabile längere Referenzen nach `docs/` verschieben.
5. Doppelte Roadmap-/Status-Inhalte nach `memory-bank/milestone.md` und `memory-bank/status.md` überführen.
6. Bekannte Lücken sichtbar in `status.md` belassen, statt sie zu verstecken.

### Mit Hilfe eines KI-Agenten

Bei einem bestehenden Projekt kann der Agent die Inventur und den ersten Memory-Bank-Entwurf übernehmen. Das funktioniert am besten, wenn das Projekt bereits nützliche README-Dateien, docs, Package-Kommentare, Tests oder CI-Dateien hat.

Warnung: Das Kopieren dieser Beispieldateien in ein bestehendes Projekt kann vorhandene `AGENTS.md`, `memory-bank/` oder `evolution/` überschreiben. Committen Sie zuerst, erstellen Sie ein Backup oder kopieren Sie die Beispiele in einen temporären Ort, bevor Sie den Agenten um das Merge bitten.

Vom Root des bestehenden Projekts aus:

```bash
cp /path/to/skills/AGENTS.md .
cp -R /path/to/skills/memory-bank .
cp -R /path/to/skills/evolution .
mkdir -p docs
```

Bitten Sie den Agenten dann, das Projekt vor dem Schreiben zu lesen:

```text
Read the existing README, docs, package README files, tests, build files, and
major source directories. Use that actual project content to fill in AGENTS.md,
memory-bank/*, and evolution/*. Preserve useful existing documentation by moving
long-form references into docs/. Keep known gaps visible in memory-bank/status.md.
Do not invent product direction that is not supported by the existing project.
```

Der Agent sollte:

1. vorhandenes Markdown und Quelllayout inventarisieren.
2. Befehle, Abhängigkeiten, Tests und Harnesses identifizieren.
3. die Memory Bank aus der aktuellen Projektrealität füllen.
4. längere Referenzen nach `docs/` verschieben oder zusammenfassen.
5. `README.md` einfach und benutzerorientiert halten.
6. ungelöste Lücken als pending- oder blocked-Zeilen in `memory-bank/status.md` belassen.

## Die Memory Bank verwenden

Mit einem Agenten wie Codex oder Claude Code kann der benutzerseitige Ablauf so einfach sein wie:

```text
tackle next pending item in memory bank
```

Der Agent sollte die nächste ausführbare Zeile in `memory-bank/status.md` finden, die Aufgabe abschließen, die erforderliche Verifikation ausführen, die Memory Bank aktualisieren und einen klar abgegrenzten git commit erstellen. Wenn diese Zeile das letzte offene Element in einem Milestone ist, sollte der Agent vor dem Weitermachen den Milestone-Review aus `memory-bank/milestone.md` ausführen. Dabei sollte er auch entscheiden, ob `evolution/` eine neue Version braucht, weil sich Produktrichtung, Architekturgrenze, Milestone-Ziel oder public/private contract wesentlich geändert haben.

Unter der Oberfläche ist der normale Agenten-Workflow:

1. `AGENTS.md` lesen.
2. Die Memory-Bank-Dateien in der von `AGENTS.md` angegebenen Reihenfolge lesen.
3. Genau eine abgegrenzte Aufgabe oder Statuszeile bearbeiten.
4. Die passende memory-bank-Datei aktualisieren, wenn sich Scope, Architecture, Tools, Milestone Acceptance oder Status geändert haben.
5. Eine Zeile erst nach bestandener Verifikation als `[+]` markieren.
6. Die Zeile als abgegrenzte Einheit committen.
7. Wenn ein Milestone vollständig wird, vor dem Weitermachen die Milestone-Review-Prozedur in `memory-bank/milestone.md` ausführen.
8. `evolution/` prüfen und nur dann eine neue Version hinzufügen, wenn der Review eine echte Änderung an Richtung, Grenze, Milestone oder Contract findet.

Statuszeilen verwenden diese Marker:

| Symbol | Bedeutung |
|---|---|
| `[ ]` | Ausstehend |
| `[+]` | Abgeschlossen |
| `[~]` | In Arbeit |
| `[!]` | Blockiert |
| `[X]` | Abgebrochen |

## Den API-Harness installieren

Der API-Harness ist kontoweit, weil er jedes Projekt steuern kann, das dieser Memory-Bank-Struktur folgt.

```bash
mkdir -p ~/.local/bin ~/.codex/prompts
cp /path/to/skills/.local/bin/tackle-memory-bank-api-loop ~/.local/bin/
cp /path/to/skills/.codex/prompts/tackle-next-memory-bank-todo.md ~/.codex/prompts/
chmod +x ~/.local/bin/tackle-memory-bank-api-loop
```

Eine Zeile ausführen:

```bash
LLM_MODEL=gpt-5.5 OPENAI_API_KEY=... MAX_RUNS=1 tackle-memory-bank-api-loop .
```

Eine Schleife ausführen:

```bash
LLM_MODEL=gpt-5.5 OPENAI_API_KEY=... MAX_RUNS=5 tackle-memory-bank-api-loop .
```

Einen OpenAI-kompatiblen Provider verwenden:

```bash
LLM_API_BASE=https://openrouter.ai/api/v1 \
LLM_API_KEY=... \
LLM_MODEL=openai/gpt-5.5 \
MAX_RUNS=1 \
tackle-memory-bank-api-loop .
```

Einen lokalen OpenAI-kompatiblen Server verwenden:

```bash
LLM_API_BASE=http://localhost:1234/v1 \
LLM_MODEL=local-model-name \
MAX_RUNS=1 \
tackle-memory-bank-api-loop .
```

Der Harness bettet die Aufgabenanweisung in seinen API-Prompt ein. Er ruft nicht die Codex CLI auf und benötigt die externe Prompt-Datei zur Laufzeit nicht. Die Prompt-Datei ist als wiederverwendbare Referenz für Menschen und Agenten enthalten.

## Was der Harness ist

Für normale Projektarbeit ist `tackle-memory-bank-api-loop` ein Ausführungs-Harness: Er führt wiederholt einen Agenten gegen ein Repository aus, gibt ihm shell-Zugriff über ein kontrolliertes Befehlsprotokoll und prüft zwischen den Läufen den git-Zustand.

Er wird nur dann Teil eines Modell-Evaluierungs-Harnesses, wenn Sie Ergebnisse über Modelle, Prompts, pass rates, review findings, cost, latency oder regressions hinweg bewerten.

Mehr lesen:

- [Ausführungs-Harness](docs/EXECUTION_de.md)
- [Modell-Evaluierungs-Harness](docs/MODEL_EVAL_de.md)

## Wartungsregeln

- `AGENTS.md` kurz halten.
- Projekt-`README.md` benutzerorientiert halten.
- Lange Erklärungen in `docs/` ablegen.
- Aktive Wahrheit in `memory-bank/` ablegen.
- Historische Richtungssnapshots in `evolution/` ablegen.
- Memory im selben commit aktualisieren wie den Code oder die docs, die sie beschreibt.
- Eine neue evolution-Version nur bei einer echten Richtungsänderung hinzufügen.
- Doppelte docs löschen, sobald nützlicher Inhalt zusammengeführt wurde.
