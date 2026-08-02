# Ein minimaler Engineering-Harness

Coding-Agenten arbeiten besser, wenn ein Projekt sich selbst erklären kann — was es ist, was fertig ist, was als Nächstes kommt. Der übliche Weg dorthin ist, ein System zu übernehmen: ein CLI, ein Scaffold, eine Reihe von Slash-Befehlen, einen Ordner generierter Artefakte. Ein halbes Jahr später pflegen Sie die Dateien dieses Systems ebenso wie Ihren eigenen Code, und Ihr Projekt lebt in dessen Konventionen statt in Ihren.

Dieses Repository setzt auf das Gegenteil. Fünf oder sechs Markdown-Dateien, in Ihr Projekt kopiert, vollständig Ihr Eigentum. Kein CLI zu installieren, kein Vokabular zu lernen, nichts verpflichtend. Löschen Sie jede davon an dem Tag, an dem sie ihren Platz nicht mehr verdient.

**Was am Ende herauskommt, gehört Ihnen.** Dieses Repository ist ein Ausgangspunkt, aus dem Sie herauskopieren — `template/` in Ihr Projekt, `harness/` optional in Ihr Home-Verzeichnis. Danach hat Ihr Projekt keine Abhängigkeit zu diesem Repository und keinen Rückverweis darauf.

Drei optionale Slash-Befehle können das Kopieren und Ausfüllen für Sie erledigen — siehe [Die drei Befehle installieren](#die-drei-befehle-installieren). An der Wette oben ändern sie nichts: Sie *erzeugen* Dateien, die Ihnen danach gehören, aktualisieren sie nie wieder, und ihr Deinstallieren lässt Ihr Projekt unberührt.

Ihr Projekt sieht am Ende so aus:

```text
your-project/
├── AGENTS.md              was ein Agent zuerst lesen soll
├── memory-bank/           was jetzt gilt
│   ├── product.md         was das ist und was nicht
│   ├── architecture.md    Layout, Datenfluss, Grenzen
│   ├── tech-stack.md      Befehle, Abhängigkeiten, Verifikation
│   ├── milestone.md       Milestones und Akzeptanzkriterien
│   └── status-M01.md      eine Datei je Milestone, eine Zeile je Aufgabe
└── evolution/             warum sich die Richtung geändert hat
```

Durchgehend meint **Harness** einen wiederholbaren Befehl, der beweist, dass etwas funktioniert — Ihre Testsuite, ein CI-Job, ein Skript. Ihr Projekt definiert seinen eigenen in `tech-stack.md`. Dieses Repository liefert zusätzlich einen optionalen Harness mit: eine API-Schleife, die einen Agenten unbeaufsichtigt durch die Memory Bank führt.

Weitere Sprachversionen: [🇬🇧 English](README.md) · [🇨🇳 中文](README_cn.md) · [🇯🇵 日本語](README_ja.md) · [🇫🇷 Français](README_fr.md) · [🇪🇸 Español](README_es.md).

## Erste Schritte

**Neu hier?** [docs/TUTORIAL.md](docs/TUTORIAL.md) führt ein Spielzeugprojekt in zwanzig Minuten vom leeren Verzeichnis zum ersten Commit — das Einrichten übernimmt `/memory-bank-init`. Der Rest dieser README ist Referenz; das Tutorial ist der geführte Weg hindurch.

**Um die Memory Bank zu nutzen, brauchen Sie `git` und sonst nichts.** Die Memory Bank ist reines Markdown, der Alltags-Workflow — einem Agenten wie Codex oder Claude Code sagen, er soll den nächsten offenen Punkt übernehmen — braucht also gar keine Laufzeitumgebung.

**Python 3 wird nur für den optionalen API-Harness gebraucht**, die unbeaufsichtigte Schleife aus [Den API-Harness installieren](#den-api-harness-installieren). Er verwendet ausschließlich die Standardbibliothek, es gibt also nichts mit `pip` zu installieren. Lassen Sie ihn ganz weg, wenn Sie die Memory Bank über einen Agenten steuern, den Sie ohnehin verwenden.

Die Anleitung für bestehende Projekte weiter unten verwendet für die erste Bestandsaufnahme zusätzlich [ripgrep](https://github.com/BurntSushi/ripgrep) (`rg`).

Klonen Sie dieses Repository einmal. Jeder `cp`-Befehl weiter unten bezeichnet Ihren Klon als `/path/to/skills`:

**Der schnellste Weg braucht gar keinen Clone.** Installieren Sie die drei Befehle und lassen Sie `/memory-bank-init` Sie befragen und die Memory Bank schreiben:

```bash
/plugin marketplace add tabilet/skills
/plugin install memory-bank
```

Führen Sie `/memory-bank-init` in Ihrem Projekt aus — leer oder bestehend — und beantworten Sie die Fragen. Das Codex-Äquivalent und die Variante mit einfachen Dateien stehen unter [Die drei Befehle installieren](#die-drei-befehle-installieren).

Um stattdessen direkt mit den Dateien zu arbeiten, klonen Sie dieses Repository einmal. Jeder `cp`-Befehl unten meint mit `/path/to/skills` Ihren Clone:

```bash
git clone https://github.com/tabilet/skills.git
cd skills
```

Aus dem Klon selbst wird nichts ausgeführt. Sie kopieren Dateien heraus: `template/` in ein Projekt, `harness/` in Ihr Home-Verzeichnis.

## Inhalt dieses Repositorys

Projektweite Beispieldateien:

- [template/AGENTS.md](template/AGENTS.md)
- [template/GOAL.md](template/GOAL.md) — das Protokoll für mehrere Milestones
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

Die drei Slash-Befehle liegen in [skills/](skills/). Claude Code und Codex lesen dasselbe `SKILL.md`-Format, es gibt also eine Quelle pro Befehl:

- [memory-bank-init](skills/memory-bank-init/SKILL.md)
- [memory-bank-next](skills/memory-bank-next/SKILL.md)
- [memory-bank-goal](skills/memory-bank-goal/SKILL.md)

`.claude-plugin/` enthält die Manifeste, mit denen sich diese als Claude-Code-Plugin installieren lassen. In `template/` liegt nichts Vendor-spezifisches.

Harness-Referenzen:

- [Ausführungs-Harness](docs/EXECUTION_de.md)
- [Modell-Evaluierungs-Harness](docs/MODEL_EVAL_de.md)

## Wie eine ausgefüllte Memory Bank aussieht

Die Vorlage enthält Platzhalter. Hier ist dieselbe Memory Bank für einen kleinen Shop-Dienst ausgefüllt, damit Sie das Ziel vor dem Weg sehen.

`memory-bank/product.md` beginnt als `[project-name] is [one or two sentences describing the project]` und wird zu:

```markdown
`cartsvc` is the shopping cart and checkout service behind the storefront.
It owns cart state, pricing, and the handoff to payments.
```

`memory-bank/milestone.md` entscheidet, wie alles andere organisiert ist — es benennt die Lanes und was jede abdeckt:

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

Danach trägt `memory-bank/status-S01.md` die Zeilen für diesen Milestone:

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

## Ein neues Projekt einrichten

Wenn Sie [die drei Befehle](#die-drei-befehle-installieren) installiert haben, erledigt `/memory-bank-init` alles in diesem Abschnitt: Es befragt Sie, schlägt Lanes und Milestones vor, wartet auf Ihre Freigabe und schreibt die Dateien dann bereits ausgefüllt. Die beiden Wege unten sind dieselbe Arbeit von Hand.

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

`/memory-bank-init` deckt diesen Fall ebenfalls ab, und zwar besser als ein Prompt aus dem Nichts: Es liest, was das Repository schon sagt — README, Tests, Build- und CI-Dateien — und fragt Sie nur nach den Entscheidungen, die daraus nicht hervorgehen; meist die Nicht-Ziele, die Grenzen und die Reihenfolge der Arbeit.

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

Es gibt drei Wege, gegen die Memory Bank zu arbeiten, und alle sind optional — die Memory Bank ist reines Markdown und funktioniert für sich allein:

| Ausführungsweg | Umfang | Braucht |
|---|---|---|
| Dem Agenten eine Anfrage tippen | Eine Zeile nach der anderen, Sie in der Schleife | Nichts |
| [`/memory-bank-next`](#die-drei-befehle-installieren) | Dasselbe, mit der vollständigen Anweisung statt Ihrer Umschreibung | Die drei Befehle |
| [Der API-Harness](#den-api-harness-installieren) | Eine Zeile pro Lauf, unbeaufsichtigt | Python 3 |
| [Eine Goal-Schleife](#mehrere-milestones-der-reihe-nach-abarbeiten) | Mehrere Milestones der Reihe nach | Ein `/goal`-Befehl |

Mit einem Agenten wie Codex oder Claude Code kann der benutzerseitige Ablauf so einfach sein wie:

```text
tackle next pending item in memory bank
```

Der Agent sollte die nächste ausführbare Zeile in `memory-bank/status-<LANE><NN>.md` finden, die Aufgabe abschließen, die erforderliche Verifikation ausführen, die Memory Bank aktualisieren und einen klar abgegrenzten git commit erstellen. Wenn diese Zeile das letzte offene Element in einem Milestone ist, sollte der Agent vor dem Weitermachen den Milestone-Review aus `memory-bank/milestone.md` ausführen. Dabei sollte er auch entscheiden, ob `evolution/` eine neue Version braucht, weil sich Produktrichtung, Architekturgrenze, Milestone-Ziel oder public/private contract wesentlich geändert haben.

Bevor Sie dem Ganzen vertrauen, geben Sie dem Agenten etwas zum Verifizieren. Tragen Sie in die Tabelle **Execution harnesses** in `memory-bank/tech-stack.md` den Befehl ein, der beweist, dass Ihr Projekt funktioniert — `make test`, `npm test`, ein Skript, was auch immer Sie ohnehin ausführen — und was ein Bestehen beweist. Eine Zeile sollte nicht auf `[+]` gehen, bevor dieser Befehl durchgelaufen ist. Ohne ihn hat „eine Zeile erst nach bestandener Verifikation abhaken“ keinen Bezugspunkt, und der Agent entscheidet selbst, was verifiziert heißt.

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

**Lanes wählen.** Eine Lane ist ein langlebiger Arbeitsstrang, kein Milestone und kein Sprint. Klassifizieren Sie nach Domäne — zu welchem Produktteil eine Änderung gehört — und nicht nach Team, Priorität oder Datum, denn Domänen überleben alle drei. Beginnen Sie nur mit `M`; trennen Sie einen Buchstaben ab, sobald eine Domäne so viel Arbeit hat, dass ihre Zeilen alles andere übertönen, oder wenn sie eine eigene Review-Kadenz braucht. Zwei oder drei Lanes sind ein normaler Dauerzustand, und ein Projekt kann lange mit einer auskommen.

Zu wenig zu trennen ist billig zu beheben: neuen Buchstaben eröffnen und neue Arbeit dort ablegen. Zu viel zu trennen nicht, denn IDs werden nach dem Anlegen der Datei nie wiederverwendet oder umbenannt — eine Lane, die Sie bereuen, bleibt für immer im Baum. Im Zweifel lassen Sie es in `M`.

Statuszeilen verwenden diese Marker:

| Symbol | Bedeutung |
|---|---|
| `[ ]` | Ausstehend |
| `[+]` | Abgeschlossen |
| `[~]` | In Arbeit |
| `[!]` | Blockiert |
| `[X]` | Abgebrochen |

### Mehrere Milestones der Reihe nach abarbeiten

Der Workflow oben rückt eine Zeile nach der anderen vor. Um mehrere Milestones in einer festgelegten Reihenfolge abzuarbeiten, ist [GOAL.md](template/GOAL.md) ein mögliches Protokoll dafür: Es gleicht vor jedem Milestone die Abhängigkeiten ab, gleicht nach dem Abschluss eines Milestones dessen nachgelagerte Milestones ab und hält an, statt zu raten, wenn eine Entscheidung oder Befugnis fehlt.

Es wird aufgerufen, nicht dauerhaft geladen. Codex und Claude Code haben beide einen `/goal`-Befehl — der von Claude Code arbeitet über Turns hinweg weiter, bis die Bedingung des Goals erfüllt ist — und die Anfrage nennt Datei und Reihenfolge:

Es wird aufgerufen, nicht dauerhaft mitgeführt. Unabhängig vom Agenten ist die Anfrage, die einen Lauf startet, immer derselbe Block — er nennt die Datei, die Reihenfolge und die Commit-Policy:

```text
Using GOAL.md, execute this loop.

STATUS_ORDER: M01 -> S01 -> A01?
COMMIT_POLICY: task
```

Wie du diesen Block sendest, unterscheidet sich, denn `/goal` ist nicht in jedem Agenten derselbe Befehl. Nutze den Abschnitt für deinen.

#### Wenn du Claude Code nutzt

`/goal` ist eingebaut und ist **kein** Weg, eine Aufgabe zu starten. Es setzt eine Stoppbedingung — „ein Ziel, das Claude vor dem Beenden prüft“ — sodass die Sitzung über mehrere Züge weiterarbeitet, statt nach einer Antwort zu enden.

Es braucht also zwei Nachrichten. Sende den Block oben als gewöhnliche Nachricht und setze dann die Bedingung, die entscheidet, wann der Lauf beendet ist:

```text
/goal every row in M01 and S01 is `[+]` and the required verification passes
```

`/goal active` zeigt die aktuelle Bedingung, `/goal clear` beendet sie vorzeitig. Die Bedingung ist auf 4000 Zeichen begrenzt, benötigt einen vertrauenswürdigen Workspace und steht nicht zur Verfügung, wenn Hooks durch Einstellungen oder Policy deaktiviert sind.

Um den Block selbst wiederverwendbar zu halten, speichere ihn als Projektbefehl — aber nicht als `.claude/commands/goal.md`, weil der eingebaute Befehl diesen Namen belegt. Nenne ihn `.claude/commands/milestones.md` und rufe ihn mit `/milestones` auf.

#### Wenn du Codex nutzt

Es gibt kein eingebautes `/goal`. Eigene Prompts sind Markdown-Dateien in `~/.codex/prompts/`, aufgerufen über den Dateinamen. Du kannst den Befehl also selbst anlegen und die Reihenfolge als Argument entgegennehmen lassen. Lege `~/.codex/prompts/goal.md` an:

```markdown
---
description: Execute an ordered set of milestones using GOAL.md.
argument-hint: M01 -> S01 -> A01?
---

Using GOAL.md, execute this loop.

STATUS_ORDER: $ARGUMENTS
COMMIT_POLICY: task
```

Dann startet eine einzige Nachricht den Lauf:

```text
/goal M01 -> S01 -> A01?
```

Das ist derselbe Mechanismus wie beim mitgelieferten Prompt [tackle-next-memory-bank-todo.md](harness/prompts/tackle-next-memory-bank-todo.md), der im selben Verzeichnis installiert wird.

#### Jeder andere Agent

Füge den Block als gewöhnliche Anfrage ein. Das Protokoll braucht nur, dass die Datei genannt wird; nichts hängt davon ab, dass ein Slash-Befehl existiert.

`COMMIT_POLICY` ist wichtig, und ein Goal-Lauf ist eine bewusste Ausnahme von der sonstigen Regel. Für die Dauer des Laufs ist es die gesamte Commit-Regel: In `AGENTS.md` mag stehen, dass jede Statuszeile eine Commit-Einheit ist, aber `COMMIT_POLICY: none` — die Vorgabe des Protokolls — bedeutet gar keine Commits, und das ist korrektes Verhalten, kein Konflikt. Schreiben Sie `task`, wenn Sie die üblichen Commits pro Zeile wollen. Die Reihenfolge ist Anfrage, dann `GOAL.md`, dann `AGENTS.md` — und nur für Commits, und nur innerhalb des Laufs.

Ein angehängtes `?` markiert einen Milestone als bedingt: Er wird übersprungen, nicht abgebrochen, wenn sein dokumentierter Auslöser fehlt.

`GOAL.md` enthält keine projektspezifischen Pfade, Lane-Buchstaben oder Befehle. Es liest sie aus `AGENTS.md` und der Memory Bank, weshalb dieselbe Datei unverändert in jedem Projekt funktioniert, das sie kopiert.

Nichts verlangt, dass Sie es verwenden. `/goal` ist der Befehl Ihres Agenten, nicht der dieses Harness — bringen Sie Ihr eigenes Protokoll mit oder gar keines, die Memory Bank verhält sich genau gleich. `GOAL.md` liegt bei, weil so ein Protokoll mühsam zu schreiben ist, nicht weil hier irgendetwas davon abhinge. Wenn Sie ein eigenes haben, richten Sie die beiden `GOAL.md`-Erwähnungen — in `AGENTS.md` und `memory-bank/milestone.md` — darauf aus oder löschen Sie sie.

## Die drei Befehle installieren

Ebenfalls optional. Alles oben funktioniert, indem du gewöhnliche Sätze tippst; diese Befehle machen die drei Momente nur wiederholbar und tragen die vollständige Anweisung statt deiner Umschreibung.

| Befehl | Wann |
|---|---|
| `/memory-bank-init` | Einmalig, in einem Projekt ohne `memory-bank/`. Es befragt dich, schlägt eine Aufteilung vor und schreibt dann die Dateien. |
| `/memory-bank-next` | Täglich. Eine Zeile umsetzen, verifizieren, committen. |
| `/memory-bank-goal` | Wenn mehrere Milestones der Reihe nach laufen sollen. |

`/memory-bank-init` verändert die Erfahrung am stärksten: Es stellt eine Frage nach der anderen, jeweils mit einer empfohlenen Antwort, schlägt alles selbst nach, was es im Repository lesen kann, und schreibt nichts, bevor du die Aufteilung freigibst. Du siehst keinen einzigen Platzhalter in eckigen Klammern — die Memory Bank kommt ausgefüllt an. (Interviewtechnik übernommen vom `grilling`-Skill aus [mattpocock/skills](https://github.com/mattpocock/skills), MIT.)

Beide Agenten lesen dasselbe `SKILL.md`-Format, es gibt also eine Quelle pro Befehl:

Beide Agenten lesen dasselbe `SKILL.md`-Format **und dasselbe Manifest**, es gibt also eine Quelle pro Befehl und ein Release zum Installieren.

**Claude Code:**

```bash
/plugin marketplace add tabilet/skills
/plugin install memory-bank
```

**Codex** hat ein eigenes Plugin-System und liest `.claude-plugin/plugin.json` als Fallback, dasselbe Repository funktioniert also:

```bash
codex plugin marketplace add tabilet/skills
codex plugin add memory-bank@tabilet
```

Codex verlangt den `@marketplace`-Zusatz, wenn ein Plugin-Name über die konfigurierten Marketplaces hinweg nicht eindeutig ist — `memory-bank@tabilet` ist daher die Form, die man sich merkt. `codex plugin marketplace upgrade` aktualisiert den Snapshot, wenn eine neue Version erscheint.

**Der Aufruf unterscheidet sich.** Claude Code registriert sie als Slash-Befehle — `/memory-bank-init`. Codex registriert sie als Skills, die über den Namen erreicht werden, also ohne Slash: „use the memory-bank-init skill“. Normale Sätze funktionieren in beiden, worauf die Memory Bank ohnehin ausgelegt ist.

**Beide Agenten** nehmen sie auch als Dateien, die Ihnen gehören, statt als verwaltetes Plugin:

```bash
mkdir -p ~/.codex/skills            # or ~/.claude/skills
curl -fsSL https://github.com/tabilet/skills/archive/refs/heads/main.tar.gz \
  | tar -xz --strip-components=2 -C ~/.codex/skills 'skills-main/skills'
```

Zum Festpinnen einer Version ersetzen Sie `refs/heads/main` durch `refs/tags/<version>` und `skills-main` durch `skills-<version>`, passend zum Verzeichnis in jenem Tarball.

Der Skill heißt bewusst nicht `goal`: Claude Code hat ein eingebautes `/goal`, das eine Stoppbedingung setzt — etwas anderes. Beide arbeiten zusammen, siehe „Mehrere Milestones der Reihe nach abarbeiten“.

### Wenn Sie bereits `/grill-me` nutzen

`/grill-me` und `/grilling` aus [mattpocock/skills](https://github.com/mattpocock/skills) enden dort, wo sie es beabsichtigen: *"Do not act on it until I confirm we have reached a shared understanding."* — handle nicht, bevor ich bestätige, dass wir ein gemeinsames Verständnis haben. Für ein allgemeines Interview ist das genau richtig, und es ist der Grund, warum jener Skill auf alles anwendbar ist.

Endet die Sitzung, endet das Verständnis mit ihr. Nichts liegt auf der Platte, nichts, was ein Agent morgen aufgreifen kann, und nichts, wogegen sich arbeiten ließe.

`/memory-bank-init` ist dieselbe Interview-Disziplin, nur auf ein bleibendes Artefakt gerichtet — eine Frage nach der anderen, jeweils mit empfohlener Antwort, Nachschlagbares wird nachgeschlagen statt gefragt. Führen Sie es **in derselben Sitzung direkt nach dem Grill** aus:

```text
/grill-me            # explore the design; no files written
/memory-bank-init    # turn those decisions into a memory bank
```

Es fragt nicht erneut, was Sie schon geklärt haben. „Fakten nachschlagen, nach Entscheidungen fragen“ gilt für das Gespräch ebenso wie für das Repository, also fällt das Interview nach einem frischen Grill kurz aus — meist bestätigen Sie nur eine vorgeschlagene Aufteilung in Lanes und Milestones.

| | Nach `/grill-me` | Nach `/memory-bank-init` |
|---|---|---|
| Wo die Entscheidungen liegen | Im Gespräch | `product.md`, `architecture.md`, `tech-stack.md` |
| Der Agent von morgen | Fängt kalt an | Liest `AGENTS.md` und weiß Bescheid |
| Nächster Schritt | Sie entscheiden | Die nächste `` `[ ]` ``-Zeile |
| Ausführung | — | `/memory-bank-next`, oder `/memory-bank-goal` für einen Satz |

Die beiden ergänzen sich, sie konkurrieren nicht. Behalten Sie `/grill-me` für Entscheidungen, aus denen kein Projekt entsteht — ein Architekturstreit, ein Einstellungsplan, ein Vortragsgerüst. Greifen Sie zu `/memory-bank-init`, wenn das, worüber Sie grillen, eine Codebasis ist, die nächste Woche noch wissen muss, was sie ist.

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

Anthropic (Claude) statt des OpenAI-kompatiblen Wegs verwenden:

```bash
LLM_PROVIDER=anthropic \
LLM_MODEL=claude-opus-5 \
ANTHROPIC_API_KEY=... \
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
