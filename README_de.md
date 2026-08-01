# Ein minimaler Engineering-Harness

Dieses Repository ist ein kopierbarer Ausgangspunkt für ein leichtgewichtiges Projekt-Betriebssystem, aufgebaut um:

- `AGENTS.md` als Bootstrap-Leitfaden für Agenten.
- `memory-bank/` als aktuelle Source of Truth des Projekts.
- `evolution/` als versionierte Historie für Richtungsänderungen.
- Ausführungs-Harnesses als wiederholbare Befehle, die beweisen, dass die Software funktioniert.
- Modell-Evaluierungs-Harnesses als wiederholbare Evaluierungen, die modellgestütztes Verhalten messen.

Ziel ist nicht mehr Dokumentationsvolumen. Ziel ist ein kompaktes Betriebshandbuch, das Menschen und Agenten gemeinsam nutzen, und das anschließend mit ausführbaren Harnesses verbunden wird.

## Erste Schritte

**Um die Memory Bank zu nutzen, brauchen Sie `git` und sonst nichts.** Die Memory Bank ist reines Markdown, der Alltags-Workflow — einem Agenten wie Codex oder Claude Code sagen, er soll den nächsten offenen Punkt übernehmen — braucht also gar keine Laufzeitumgebung.

**Python 3 wird nur für den optionalen API-Harness gebraucht**, die unbeaufsichtigte Schleife aus [Den API-Harness installieren](#den-api-harness-installieren). Er verwendet ausschließlich die Standardbibliothek, es gibt also nichts mit `pip` zu installieren. Lassen Sie ihn ganz weg, wenn Sie die Memory Bank über einen Agenten steuern, den Sie ohnehin verwenden.

Die Anleitung für bestehende Projekte weiter unten verwendet für die erste Bestandsaufnahme zusätzlich [ripgrep](https://github.com/BurntSushi/ripgrep) (`rg`).

Klonen Sie dieses Repository einmal. Jeder `cp`-Befehl weiter unten bezeichnet Ihren Klon als `/path/to/skills`:

```bash
git clone https://github.com/tabilet/skills.git
cd skills
```

Aus dem Klon selbst wird nichts ausgeführt. Sie kopieren Dateien heraus: `template/` in ein Projekt, `harness/` in Ihr Home-Verzeichnis.

## Inhalt dieses Repositorys

Projektweite Beispieldateien:

- [template/AGENTS.md](template/AGENTS.md)
- [template/memory-bank/product.md](template/memory-bank/product.md)
- [template/memory-bank/architecture.md](template/memory-bank/architecture.md)
- [template/memory-bank/tech-stack.md](template/memory-bank/tech-stack.md)
- [template/memory-bank/milestone.md](template/memory-bank/milestone.md)
- [template/memory-bank/status-M01.md](template/memory-bank/status-M01.md)
- [template/evolution/prompt-v1.md](template/evolution/prompt-v1.md)
- [template/evolution/result-v1.md](template/evolution/result-v1.md)

Beispieldateien auf Benutzerkonto-Ebene:

- [harness/tackle-memory-bank-api-loop](harness/tackle-memory-bank-api-loop)
- [harness/prompts/tackle-next-memory-bank-todo.md](harness/prompts/tackle-next-memory-bank-todo.md)

Harness-Referenzen:

- [Ausführungs-Harness](docs/EXECUTION_de.md)
- [Modell-Evaluierungs-Harness](docs/MODEL_EVAL_de.md)

## Ein neues Projekt einrichten

### Manuell

Vom Root eines neuen Projekts aus:

```bash
cp -R /path/to/skills/template/. .
mkdir -p docs
```

Bearbeiten Sie die kopierten Dateien anschließend in dieser Reihenfolge:

1. `memory-bank/product.md`: definieren, was das Projekt ist und was nicht.
2. `memory-bank/architecture.md`: Layout, Datenfluss und Grenzen definieren.
3. `memory-bank/tech-stack.md`: Befehle, Abhängigkeiten und Harnesses definieren.
4. `memory-bank/milestone.md`: den ersten Milestone definieren.
5. `memory-bank/status-M01.md`: die ersten ausführbaren Zeilen definieren. Siehe unten „Wie eine ausgefüllte Statusdatei aussieht“ — die Backticks um die Marker sind entscheidend.
6. `evolution/prompt-v1.md`: die Anfangsrichtung festhalten.
7. `evolution/result-v1.md`: den aktuellen Startzustand festhalten.
8. `AGENTS.md`: Platzhalter durch projektspezifische Befehle und Regeln ersetzen.

Halten Sie `README.md` einfach und benutzerorientiert. Längere Referenzen gehören in `docs/`.

### Ihren Agenten anbinden

`AGENTS.md` ist ein [offener herstellerübergreifender Standard](https://agents.md), betreut von der Agentic AI Foundation. Die meisten Coding-Agenten lesen die Datei ohne jede Einrichtung, darunter Codex, Cursor, Gemini CLI, GitHub Copilot, Devin, Windsurf, Jules, Junie, Zed, Aider, VS Code, Warp, goose, opencode, Amp.

In `template/` liegt bewusst keine herstellerspezifische Datei. Wenn Ihr Agent einen anderen Dateinamen liest, verbinden Sie ihn mit einer Zeile mit `AGENTS.md`, statt eine zweite Kopie zu pflegen, die auseinanderläuft:

| Agent | Brücke |
|---|---|
| Alles aus der Liste oben | Nichts zu tun |
| Claude Code | `ln -s AGENTS.md CLAUDE.md`, oder eine `CLAUDE.md` mit `@AGENTS.md` |
| Andere Tools mit eigener Datei | Genauso per Symlink oder Import auf `AGENTS.md` zeigen |

Unter Windows brauchen Symlinks Administratorrechte oder den Entwicklermodus — dort ist die Import-Variante besser.

### Mit Hilfe eines KI-Agenten

Für ein neues Projekt können Sie die Beispieldateien als Anfangsstruktur verwenden und einen KI-Agenten bitten, sie auszufüllen, nachdem Sie das Produkt beschrieben haben.

Warnung: Das Kopieren dieser Dateien über ein bestehendes Projekt kann vorhandene Dateien auf der Festplatte überschreiben. Erstellen Sie zuerst ein Backup oder committen Sie die aktuelle Arbeit.

Vom Root des neuen Projekts aus:

```bash
cp -R /path/to/skills/template/. .
mkdir -p docs
```

Sprechen Sie dann mit dem Agenten, bis Produkt, Benutzer, Grenzen, Befehle und erster Milestone klar sind. Bitten Sie ihn, Folgendes auszufüllen:

- `AGENTS.md`
- `memory-bank/product.md`
- `memory-bank/architecture.md`
- `memory-bank/tech-stack.md`
- `memory-bank/milestone.md`
- `memory-bank/status-M01.md`
- `evolution/prompt-v1.md`
- `evolution/result-v1.md`

Beispiel-Prompt:

```text
Read the sample AGENTS.md, memory-bank/*, and evolution/* files. Based on our
discussion of this new project, replace the placeholders with accurate project
content. Keep README user-facing, put long-form references in docs/, define the status
ID lanes in memory-bank/milestone.md, and make memory-bank/status-M01.md contain
the first actionable milestone rows.
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
2. `template/` aus diesem Repository kopieren.
3. Die Memory Bank aus dem füllen, was das Projekt bereits sagt, nicht aus einer ausgedachten Neuausrichtung.
4. Stabile längere Referenzen nach `docs/` verschieben.
5. Doppelte Roadmap-/Status-Inhalte nach `memory-bank/milestone.md` und `memory-bank/status-<LANE><NN>.md` überführen.
6. Bekannte Lücken sichtbar in `status-<LANE><NN>.md` belassen, statt sie zu verstecken.

### Mit Hilfe eines KI-Agenten

Bei einem bestehenden Projekt kann der Agent die Inventur und den ersten Memory-Bank-Entwurf übernehmen. Das funktioniert am besten, wenn das Projekt bereits nützliche README-Dateien, docs, Package-Kommentare, Tests oder CI-Dateien hat.

Warnung: Das Kopieren dieser Beispieldateien in ein bestehendes Projekt kann vorhandene `AGENTS.md`, `memory-bank/` oder `evolution/` überschreiben. Committen Sie zuerst, erstellen Sie ein Backup oder kopieren Sie die Beispiele in einen temporären Ort, bevor Sie den Agenten um das Merge bitten.

Vom Root des bestehenden Projekts aus:

```bash
cp -R /path/to/skills/template/. .
mkdir -p docs
```

Bitten Sie den Agenten dann, das Projekt vor dem Schreiben zu lesen:

```text
Read the existing README, docs, package README files, tests, build files, and
major source directories. Use that actual project content to fill in AGENTS.md,
memory-bank/*, and evolution/*. Preserve useful existing documentation by moving
long-form references into docs/. Keep known gaps visible in the matching
memory-bank/status-<LANE><NN>.md file.
Do not invent product direction that is not supported by the existing project.
```

Der Agent sollte:

1. vorhandenes Markdown und Quelllayout inventarisieren.
2. Befehle, Abhängigkeiten, Tests und Harnesses identifizieren.
3. die Memory Bank aus der aktuellen Projektrealität füllen.
4. längere Referenzen nach `docs/` verschieben oder zusammenfassen.
5. `README.md` einfach und benutzerorientiert halten.
6. ungelöste Lücken als pending- oder blocked-Zeilen in `memory-bank/status-<LANE><NN>.md` belassen.

## Die Memory Bank verwenden

Mit einem Agenten wie Codex oder Claude Code kann der benutzerseitige Ablauf so einfach sein wie:

```text
tackle next pending item in memory bank
```

Der Agent sollte die nächste ausführbare Zeile in `memory-bank/status-<LANE><NN>.md` finden, die Aufgabe abschließen, die erforderliche Verifikation ausführen, die Memory Bank aktualisieren und einen klar abgegrenzten git commit erstellen. Wenn diese Zeile das letzte offene Element in einem Milestone ist, sollte der Agent vor dem Weitermachen den Milestone-Review aus `memory-bank/milestone.md` ausführen. Dabei sollte er auch entscheiden, ob `evolution/` eine neue Version braucht, weil sich Produktrichtung, Architekturgrenze, Milestone-Ziel oder public/private contract wesentlich geändert haben.

Unter der Oberfläche ist der normale Agenten-Workflow:

1. `AGENTS.md` lesen.
2. Die Memory-Bank-Dateien in der von `AGENTS.md` angegebenen Reihenfolge lesen.
3. Genau eine abgegrenzte Aufgabe oder Statuszeile bearbeiten.
4. Die passende memory-bank-Datei aktualisieren, wenn sich Scope, Architecture, Tools, Milestone Acceptance oder Status geändert haben.
5. Eine Zeile erst nach bestandener Verifikation als `[+]` markieren.
6. Die Zeile als abgegrenzte Einheit committen.
7. Wenn ein Milestone vollständig wird, vor dem Weitermachen die Milestone-Review-Prozedur in `memory-bank/milestone.md` ausführen.
8. `evolution/` prüfen und nur dann eine neue Version hinzufügen, wenn der Review eine echte Änderung an Richtung, Grenze, Milestone oder Contract findet.

### Status-ID-Lanes

Statusdateien heißen `memory-bank/status-<LANE><NN>.md`. Der Lane-Buchstabe klassifiziert die Arbeit, die Nummer ist zweistellig mit führender Null: Buchhaltungs-Milestones werden zu `status-A01.md` und `status-A02.md`, Shopping-Milestones zu `status-S01.md`. `M` ist die Standard-Lane für Arbeit, die sich keiner Domänen-Lane zuordnen lässt. Eine Lane fasst höchstens 99 Dateien; ist sie voll, eröffnen Sie einen neuen Buchstaben, statt eine dritte Ziffer hinzuzufügen. `memory-bank/milestone.md` hält fest, was jeder Buchstabe bedeutet, und verhindert die Wiederverwendung einer ID.

Statuszeilen verwenden diese Marker:

| Symbol | Bedeutung |
|---|---|
| `[ ]` | Ausstehend |
| `[+]` | Abgeschlossen |
| `[~]` | In Arbeit |
| `[!]` | Blockiert |
| `[X]` | Abgebrochen |

### Wie eine ausgefüllte Statusdatei aussieht

Die Vorlagen enthalten Platzhalter. Für einen kleinen Shop-Dienst ausgefüllt, sieht `memory-bank/status-S01.md` so aus:

```markdown
# Status S01 - Cart And Checkout

| Item | State | Notes |
|---|---|---|
| Add POST /cart endpoint | `[+]` | Verified by tests/cart_test.py. |
| Cart total calculation | `[~]` | Rounding rules still open. |
| Wire cart to checkout | `[ ]` | Blocked on the A02 payment contract. |
| Guest checkout | `[X]` | Cancelled; accounts required at launch. |
```

**Die Backticks um jeden Marker sind erforderlich.** Der Harness trifft auf `` `[ ]` `` zu, nicht auf `[ ]`. Eine Zeile wie `| Item | [ ] | Notes |` wird stillschweigend ignoriert: Der Harness meldet „No actionable memory-bank rows remain“ und endet erfolgreich, als wäre die Arbeit erledigt.

Für den Rest der Memory Bank gilt dasselbe Ersetzen der Platzhalter. `memory-bank/product.md` beginnt als `[project-name] is [one or two sentences describing the project]` und wird zu:

```markdown
`cartsvc` is the shopping cart and checkout service behind the storefront.
It owns cart state, pricing, and the handoff to payments.
```


## Den API-Harness installieren

Dieser Abschnitt ist optional. Alles oben funktioniert auch ohne ihn — der Harness ergänzt lediglich eine unbeaufsichtigte Schleife, die einen Agenten über die API steuert, statt dass Sie selbst tippen. Lassen Sie ihn weg, wenn Codex, Claude Code oder ein anderer Agent das bereits für Sie erledigt.

Der API-Harness ist kontoweit, weil er jedes Projekt steuern kann, das dieser Memory-Bank-Struktur folgt. Er braucht Python 3 und sonst nichts.

```bash
mkdir -p ~/.local/bin ~/.codex/prompts
cp /path/to/skills/harness/tackle-memory-bank-api-loop ~/.local/bin/
cp /path/to/skills/harness/prompts/tackle-next-memory-bank-todo.md ~/.codex/prompts/
chmod +x ~/.local/bin/tackle-memory-bank-api-loop
```

Die Befehle unten rufen `tackle-memory-bank-api-loop` über den Namen auf; dafür muss `~/.local/bin` in Ihrem `PATH` liegen. Wenn `command -v tackle-memory-bank-api-loop` nichts ausgibt, fügen Sie diese Zeile Ihrem Shell-Profil hinzu:

```bash
export PATH="$HOME/.local/bin:$PATH"
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

### Der erste Lauf

Ein Lauf gibt zuerst Repository, Provider, Modell und API-Endpunkt aus und bearbeitet dann eine Zeile:

```text
Repo: /path/to/your-project
Provider: anthropic
Model: claude-opus-5
API: https://api.anthropic.com/v1/messages
Run 1/1: asking LLM to tackle one row.
  LLM turn 1/60
  shell: sed -n '1,120p' AGENTS.md  # Read the bootstrap guide.
```

Der Harness stoppt absichtlich früh, und sein Exit-Code sagt warum. `3` bis `7` sind normale Stoppbedingungen und keine Fehler — `4` bedeutet etwa, dass der Worktree vor dem Lauf nicht sauber war, und `6`, dass der Agent ohne Commit fertig wurde. `11` bedeutet, dass keine `status-<LANE><NN>.md`-Dateien gefunden wurden, was meist heißt, dass die Memory Bank noch nicht ausgefüllt ist. Die vollständige Tabelle steht im [Ausführungs-Harness](docs/EXECUTION_de.md#exit-codes).

## Was der Harness ist

Für normale Projektarbeit ist `tackle-memory-bank-api-loop` ein Ausführungs-Harness: Er führt wiederholt einen Agenten gegen ein Repository aus, gibt ihm shell-Zugriff über ein kontrolliertes Befehlsprotokoll und prüft zwischen den Läufen den git-Zustand.

Er findet jede `memory-bank/status-<LANE><NN>.md`-Datei, meldet je Lane die Anzahl ausführbarer und blockierter Zeilen und lässt den Agenten die nächste Zeile anhand der Lane-Bedeutungen und der Milestone-Priorität wählen. Eine blockierte Zeile in einer Lane hält die Arbeit in den anderen nicht auf; die Schleife stoppt zur menschlichen Prüfung erst, wenn nur noch blockierte Zeilen übrig sind.

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
