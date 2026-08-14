# Ein minimaler Engineering-Harness

Coding-Agenten arbeiten besser, wenn ein Projekt sich selbst erklären kann: was es ist, was fertig ist und was als Nächstes kommt. Dieses Repository gibt Ihnen eine kleine Gruppe einfacher Textdateien, überwiegend Markdown, die genau das leisten. Sie kopieren sie in Ihr Projekt und besitzen sie von diesem Moment an.

Alles hier ist einfacher Text, deshalb brauchen Sie nur `git`. Sie können die Dateien lesen, von Hand bearbeiten, umbenennen oder löschen, und jeder Agent, der Markdown liest, kann mit ihnen arbeiten. Ein optionales Plugin erzeugt die Dateien für Sie, und ein optionaler API-Runner arbeitet sie unbeaufsichtigt ab; beide bleiben außerhalb Ihres Projekts.

`template/` kommt in Ihr Projekt, `harness/` in Ihr Home-Verzeichnis, wenn Sie den API-Runner möchten. Sobald die Dateien liegen, gehören sie Ihrem Projekt, und Ihr Projekt bleibt von diesem Repository unabhängig. Ein halbes Jahr später pflegen Sie immer noch nur Ihren eigenen Code.

Drei optionale Skills können das Kopieren und Ausfüllen für Sie erledigen; siehe [Die drei Befehle installieren](#die-drei-befehle-installieren). Die Dateien, die sie schreiben, gehören Ihnen von dem Moment an, in dem sie erscheinen, und sie bleiben genau so, wie Sie sie hinterlassen.

Ihr Projekt sieht am Ende so aus:

```text
your-project/
├── AGENTS.md              was ein Agent zuerst lesen soll
├── GOAL.md                optionales Protokoll für mehrere Milestones
├── memory-bank/           was jetzt gilt
│   ├── product.md         was das ist und was nicht
│   ├── architecture.md    Layout, Datenfluss, Grenzen
│   ├── tech-stack.md      Befehle, Abhängigkeiten, Verifikation
│   ├── milestone.md       Milestones und Akzeptanzkriterien
│   ├── status-M01.md      eine dauerhafte Datei je Milestone, eine Zeile je Aufgabe
│   └── suggested.txt      verwerfbare Startreferenz für mehrere Milestones
└── evolution/             versionierte Richtungssnapshots
    ├── prompt-v1.md       die anfängliche Richtung
    └── result-v1.md       der daraus entstandene Zustand
```

Der Begriff *Memory Bank* wurde von [Cline](https://docs.cline.bot/best-practices/memory-bank) populär gemacht; dies ist eine andere Umsetzung derselben Idee, in reinen Dateien ohne Runtime.

Durchgehend meint **Harness** einen wiederholbaren Befehl, der beweist, dass etwas funktioniert, etwa Ihre Testsuite, einen CI-Job oder ein Skript. Ihr Projekt definiert seinen eigenen in `tech-stack.md`. Dieses Repository liefert zusätzlich einen optionalen Harness mit: eine API-Schleife, die einen Agenten unbeaufsichtigt durch die Memory Bank führt.

Weitere Sprachversionen: [🇬🇧 English](README.md) · [🇨🇳 中文](README_cn.md) · [🇯🇵 日本語](README_ja.md) · [🇫🇷 Français](README_fr.md) · [🇪🇸 Español](README_es.md).

## Erste Schritte

**Neu hier?** [docs/TUTORIAL.md](docs/TUTORIAL.md) führt ein Spielzeugprojekt in zwanzig Minuten vom leeren Verzeichnis zum ersten Commit, wobei `memory-bank-init` das Einrichten übernimmt. Der Rest dieser README ist Referenzmaterial, und das Tutorial ist ein geführter Weg hindurch.

Die Memory Bank braucht `git` und sonst nichts. Sie ist reines Markdown, der Alltags-Workflow braucht also keine Laufzeitumgebung: Sie sagen einem Agenten wie Codex oder Claude Code, er soll den nächsten offenen Punkt übernehmen, und er bearbeitet die Dateien direkt.

**Python 3 wird nur für den optionalen API-Harness gebraucht**, die unbeaufsichtigte Schleife aus [Den API-Harness installieren](#den-api-harness-installieren). Er verwendet ausschließlich die Standardbibliothek, es gibt also nichts mit `pip` zu installieren. Lassen Sie ihn ganz weg, wenn Sie die Memory Bank über einen Agenten steuern, den Sie ohnehin verwenden.

Die Anleitung für bestehende Projekte weiter unten verwendet für die erste Bestandsaufnahme zusätzlich [ripgrep](https://github.com/BurntSushi/ripgrep) (`rg`).

Der schnellste Einstieg kommt ganz ohne Clone aus. Installieren Sie das Plugin und lassen Sie dessen namespaced `memory-bank-init`-Skill Sie befragen und die Memory Bank für Sie schreiben:

```bash
/plugin marketplace add tabilet/skills
/plugin install memory-bank
/memory-bank:memory-bank-init
```

Führen Sie diese Befehle in Claude Code in Ihrem Projekt aus, ob es leer ist oder schon Code enthält, und beantworten Sie die Fragen. Das Codex-Äquivalent und die Variante mit einfachen Dateien stehen unter [Die drei Befehle installieren](#die-drei-befehle-installieren).

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

Der optionale API-Runner und seine nur im Repository liegende menschenlesbare Anweisungskopie:

- [harness/tackle-memory-bank-api-loop](harness/tackle-memory-bank-api-loop)
- [harness/prompts/tackle-next-memory-bank-todo.md](harness/prompts/tackle-next-memory-bank-todo.md)

Die drei Skills liegen in [skills/](skills/). Claude Code und Codex lesen dasselbe `SKILL.md`-Format, es gibt also eine Quelle pro Skill:

- [memory-bank-init](skills/memory-bank-init/SKILL.md)
- [memory-bank-next](skills/memory-bank-next/SKILL.md)
- [memory-bank-goal](skills/memory-bank-goal/SKILL.md)

`.claude-plugin/` enthält das Kompatibilitätsmanifest, mit dem sich dasselbe Plugin in Claude Code und Codex installieren lässt. In `template/` liegt nichts Vendor-spezifisches.

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

`memory-bank/milestone.md` entscheidet, wie alles andere organisiert ist. Es benennt die Lanes und nennt, was jede abdeckt:

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

Wenn Sie [die drei Befehle](#die-drei-befehle-installieren) installiert haben, erledigt `memory-bank-init` alles in diesem Abschnitt: Es befragt Sie, schlägt Lanes und Milestones vor, wartet auf Ihre Freigabe und schreibt die Dateien dann bereits ausgefüllt. Die beiden Wege unten sind dieselbe Arbeit von Hand.

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
5. `memory-bank/status-M01.md`: die ersten ausführbaren Zeilen definieren. Siehe unten „Wie eine ausgefüllte Statusdatei aussieht“, und beachten Sie, dass die Backticks um die Marker entscheidend sind.
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

Unter Windows brauchen Symlinks Administratorrechte oder den Entwicklermodus, deshalb ist dort die Import-Variante besser.

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

`memory-bank-init` deckt diesen Fall ebenfalls ab, und zwar besser als ein Prompt aus dem Nichts: Es liest, was das Repository schon sagt, also README, Tests sowie Build- und CI-Dateien, und fragt Sie dann nur nach den Entscheidungen, die daraus nicht hervorgehen: meist die Nicht-Ziele, die Grenzen und die Reihenfolge der Arbeit.

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

Es gibt vier Wege, gegen die Memory Bank zu arbeiten, und alle sind optional, denn die Memory Bank ist reines Markdown und funktioniert für sich allein:

| Ausführungsweg | Umfang | Braucht |
|---|---|---|
| Dem Agenten eine Anfrage tippen | Eine Zeile nach der anderen, Sie in der Schleife | Nichts |
| [`memory-bank-next`](#die-drei-befehle-installieren) | Dasselbe, mit der vollständigen Anweisung statt Ihrer Umschreibung | Die optionalen Skills |
| [Der API-Harness](#den-api-harness-installieren) | Eine Zeile pro Lauf, unbeaufsichtigt | Python 3 |
| [Eine Goal-Schleife](#mehrere-milestones-der-reihe-nach-abarbeiten) | Mehrere Milestones der Reihe nach | `GOAL.md` und eine normale Anfrage oder ein optionaler Skill |

Mit einem Agenten wie Codex oder Claude Code kann der benutzerseitige Ablauf so einfach sein wie:

```text
tackle next pending item in memory bank
```

Der Agent sollte die nächste ausführbare Zeile in `memory-bank/status-<LANE><NN>.md` finden, die Aufgabe abschließen, die erforderliche Verifikation ausführen, die Memory Bank aktualisieren und einen klar abgegrenzten git commit erstellen. Wenn diese Zeile das letzte offene Element in einem Milestone ist, sollte der Agent vor dem Weitermachen den Milestone-Review aus `memory-bank/milestone.md` ausführen. Änderungen aus dem Review werden committet; ohne Änderungen entsteht kein leerer Milestone-Commit. Dabei sollte er auch entscheiden, ob `evolution/` eine neue Version braucht, weil sich Produktrichtung, Architekturgrenze, Milestone-Ziel oder public/private contract wesentlich geändert haben.

Bevor Sie dem Ganzen vertrauen, geben Sie dem Agenten etwas zum Verifizieren. Tragen Sie in die Tabelle **Execution harnesses** in `memory-bank/tech-stack.md` den Befehl ein, der beweist, dass Ihr Projekt funktioniert, etwa `make test`, `npm test` oder ein Skript, das Sie ohnehin ausführen, und halten Sie fest, was ein Bestehen beweist. Eine Zeile sollte nicht auf `[+]` gehen, bevor dieser Befehl durchgelaufen ist. Ohne ihn hat „eine Zeile erst nach bestandener Verifikation abhaken“ keinen Bezugspunkt, und der Agent entscheidet selbst, was verifiziert heißt.

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

**Lanes wählen.** Eine Lane ist ein langlebiger Arbeitsstrang, im Maßstab eher ein Produktbereich als ein Milestone oder ein Sprint. Klassifizieren Sie nach Domäne, also danach, zu welchem Produktteil eine Änderung gehört, denn Domänen überleben Teams, Prioritäten und Daten. Beginnen Sie nur mit `M`; trennen Sie einen Buchstaben ab, sobald eine Domäne so viel Arbeit hat, dass ihre Zeilen alles andere übertönen, oder wenn sie eine eigene Review-Kadenz braucht. Zwei oder drei Lanes sind ein normaler Dauerzustand, und ein Projekt kann lange mit einer auskommen.

Zu wenig zu trennen ist billig zu beheben: neuen Buchstaben eröffnen und neue Arbeit dort ablegen. Zu viel zu trennen ist dauerhaft, denn eine ID behält ihren Namen für die Lebensdauer des Projekts, sobald ihre Datei existiert. Im Zweifel lassen Sie es in `M`.

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

Es wird aufgerufen, nicht dauerhaft mitgeführt. Unabhängig vom Agenten ist die Anfrage, die einen Lauf startet, immer derselbe Block, und er nennt die Datei, die Reihenfolge und die Commit-Policy:

```text
Using GOAL.md, execute this loop.

STATUS_ORDER: M01 -> S01 -> A01?
COMMIT_POLICY: task
```

Wenn `memory-bank-init` das Projekt erstellt hat, schreibt es außerdem die
vollständige vorgeschlagene Anfrage mit `STATUS_ORDER`, `STATUS_FILE_MAP` und
`DOWNSTREAM_IMPACTS` nach `memory-bank/suggested.txt`. Die Datei ist eine
verwerfbare Startreferenz, keine zweite Roadmap. Gleichen Sie sie vor Gebrauch
mit `milestone.md` und den aktuellen Statusdateien ab und löschen Sie sie nach
dem Start oder sobald sie veraltet ist:

```text
Using GOAL.md, reconcile memory-bank/suggested.txt against the current memory bank, then execute the resolved loop.
COMMIT_POLICY: task
```

Den Block oben können Sie jedem Agenten als gewöhnliche Anfrage senden. Mit dem Plugin startet dasselbe Protokoll über `/memory-bank:memory-bank-goal M01 -> S01 -> A01?` in Claude Code oder `$memory-bank:memory-bank-goal M01 -> S01 -> A01?` in Codex. Direkt installierte Skills verwenden `/memory-bank-goal` beziehungsweise `$memory-bank-goal`.

Ohne Argumente gleicht der Goal-Skill bevorzugt eine gültige `suggested.txt` ab und zeigt die vollständig aufgelöste Anfrage zur Bestätigung. Fehlt die Datei oder ist sie veraltet, leitet er die Reihenfolge aus `milestone.md` ab.

#### Wenn du Claude Code nutzt

Claude Codes eingebautes `/goal` ist ein optionaler alternativer Starter für lange Läufe. Geben Sie die vollständige Protokollanfrage, Commit-Policy und messbare Abschlussbedingung gemeinsam an:

```text
/goal Using GOAL.md, reconcile memory-bank/suggested.txt against the current memory bank, then execute the resolved loop. COMMIT_POLICY: task. Completion condition: every required status is complete, every triggered conditional status is complete, and every milestone's documented verification passes.
```

`/goal` ohne Argumente zeigt den Status, `/goal clear` beendet den Lauf. Der Skill `memory-bank-goal` bleibt der mit Codex gemeinsam nutzbare portable Starter.

#### Wenn du Codex nutzt

Rufen Sie den Plugin-Skill direkt auf:

```text
$memory-bank:memory-bank-goal M01 -> S01 -> A01?
```

Bei direkt installierten Skill-Dateien verwenden Sie `$memory-bank-goal M01 -> S01 -> A01?`. Codex Custom Prompts sind zugunsten von Skills veraltet; dieses Repository installiert oder empfiehlt daher keinen separaten `goal.md`-Prompt mehr.

#### Jeder andere Agent

Füge den Block als gewöhnliche Anfrage ein. Das Protokoll braucht nur, dass die Datei genannt wird; nichts hängt davon ab, dass ein Slash-Befehl existiert.

`COMMIT_POLICY` ist wichtig, und ein Goal-Lauf ist eine bewusste Ausnahme von der sonstigen Regel. Für die Dauer des Laufs ist es die gesamte Commit-Regel: In `AGENTS.md` mag stehen, dass jede Statuszeile eine Commit-Einheit ist, aber `COMMIT_POLICY: none`, die Vorgabe des Protokolls, bedeutet gar keine Commits. Das ist korrektes Verhalten und kein Konflikt. Schreiben Sie `task`, wenn Sie die üblichen Commits pro Zeile wollen. Die Reihenfolge ist Anfrage, dann `GOAL.md`, dann `AGENTS.md`, und das gilt nur für Commits und nur innerhalb des Laufs.

Ein angehängtes `?` markiert einen Milestone als bedingt: Er wird übersprungen, nicht abgebrochen, wenn sein dokumentierter Auslöser fehlt.

`GOAL.md` enthält keine projektspezifischen Pfade, Lane-Buchstaben oder Befehle. Es liest sie aus `AGENTS.md` und der Memory Bank, weshalb dieselbe Datei unverändert in jedem Projekt funktioniert, das sie kopiert.

Nichts verlangt, dass Sie es verwenden. Bringen Sie Ihr eigenes Protokoll mit oder gar keines; die Memory Bank verhält sich genau gleich. `GOAL.md` liegt bei, weil so ein Protokoll mühsam zu schreiben ist, nicht weil hier irgendetwas davon abhinge. Wenn Sie ein eigenes haben, richten Sie die beiden `GOAL.md`-Erwähnungen darauf aus oder löschen Sie sie. Sie stehen in `AGENTS.md` und `memory-bank/milestone.md`.

## Die drei Befehle installieren

Ebenfalls optional. Alles oben funktioniert, indem du gewöhnliche Sätze tippst; diese Befehle machen die drei Momente nur wiederholbar und tragen die vollständige Anweisung statt deiner Umschreibung.

| Befehl | Wann |
|---|---|
| `memory-bank-init` | Einmalig, in einem Projekt ohne `memory-bank/`. Es befragt dich, schlägt eine Aufteilung vor und schreibt dann die Dateien. |
| `memory-bank-next` | Täglich. Eine Zeile umsetzen, verifizieren, committen. |
| `memory-bank-goal` | Wenn mehrere Milestones der Reihe nach laufen sollen. |

`memory-bank-init` verändert die Erfahrung am stärksten: Es stellt eine Frage nach der anderen, jeweils mit einer empfohlenen Antwort, schlägt alles selbst nach, was es im Repository lesen kann, und schreibt nichts, bevor Sie die Aufteilung freigeben. Sie sehen keinen einzigen Platzhalter in eckigen Klammern, denn die Memory Bank kommt ausgefüllt an. (Interviewtechnik übernommen vom `grilling`-Skill aus [mattpocock/skills](https://github.com/mattpocock/skills), MIT.)

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

Codex verlangt den `@marketplace`-Zusatz, wenn ein Plugin-Name über die konfigurierten Marketplaces hinweg nicht eindeutig ist, deshalb ist `memory-bank@tabilet` die Form, die man sich merkt. `codex plugin marketplace upgrade` aktualisiert den Snapshot, wenn eine neue Version erscheint.

**Plugin-Aufrufe sind namespaced.** Claude Code verwendet `/memory-bank:memory-bank-init`, `/memory-bank:memory-bank-next` und `/memory-bank:memory-bank-goal`; Codex verwendet `$memory-bank:memory-bank-init`, `$memory-bank:memory-bank-next` und `$memory-bank:memory-bank-goal`. Normale Sätze funktionieren weiterhin in beiden.

**Beide Agenten** nehmen sie auch als Dateien, die Ihnen gehören, statt als verwaltetes Plugin:

```bash
mkdir -p ~/.agents/skills
curl -fsSL https://github.com/tabilet/skills/archive/refs/heads/main.tar.gz \
  | tar -xz --strip-components=2 -C ~/.agents/skills 'skills-main/skills'

# Claude Code alternative
mkdir -p ~/.claude/skills
curl -fsSL https://github.com/tabilet/skills/archive/refs/heads/main.tar.gz \
  | tar -xz --strip-components=2 -C ~/.claude/skills 'skills-main/skills'
```

Direkt installierte Skill-Dateien sind nicht namespaced: `/memory-bank-init` in Claude Code und `$memory-bank-init` in Codex; für die beiden anderen Skills gilt dasselbe Muster.

Zum Festpinnen einer Version ersetzen Sie `refs/heads/main` durch `refs/tags/<version>` und `skills-main` durch `skills-<version>`, passend zum Verzeichnis in jenem Tarball.

Der Skill heißt bewusst nicht `goal`: Claude Code hat ein eingebautes `/goal`, das eine Stoppbedingung setzt und damit etwas anderes tut. Beide arbeiten zusammen, siehe „Mehrere Milestones der Reihe nach abarbeiten“.

### Wenn Sie bereits `/grill-me` nutzen

`/grill-me` und `/grilling` aus [mattpocock/skills](https://github.com/mattpocock/skills) enden dort, wo sie es beabsichtigen: *"Do not act on it until I confirm we have reached a shared understanding."* (handle nicht, bevor ich bestätige, dass wir ein gemeinsames Verständnis haben). Für ein allgemeines Interview ist das genau richtig, und es ist der Grund, warum jener Skill auf alles anwendbar ist.

Endet die Sitzung, endet das Verständnis mit ihr. Nichts liegt auf der Platte, nichts, was ein Agent morgen aufgreifen kann, und nichts, wogegen sich arbeiten ließe.

`memory-bank-init` ist dieselbe Interview-Disziplin, nur auf ein bleibendes Artefakt gerichtet. Es stellt eine Frage nach der anderen, jeweils mit empfohlener Antwort, und schlägt Nachschlagbares nach, statt danach zu fragen. Führen Sie es **in derselben Sitzung direkt nach dem Grill** aus:

```text
/grill-me            # explore the design; no files written
/memory-bank:memory-bank-init    # Claude Code plugin
$memory-bank:memory-bank-init    # Codex plugin
```

Es fragt nicht erneut, was Sie schon geklärt haben. „Fakten nachschlagen, nach Entscheidungen fragen“ gilt für das Gespräch ebenso wie für das Repository, also fällt das Interview nach einem frischen Grill kurz aus, und meist bestätigen Sie nur eine vorgeschlagene Aufteilung in Lanes und Milestones.

| | Nach `/grill-me` | Nach `memory-bank-init` |
|---|---|---|
| Wo die Entscheidungen liegen | Im Gespräch | `product.md`, `architecture.md`, `tech-stack.md` |
| Der Agent von morgen | Fängt kalt an | Liest `AGENTS.md` und weiß Bescheid |
| Nächster Schritt | Sie entscheiden | Die nächste `` `[ ]` ``-Zeile |
| Ausführung | — | `memory-bank-next`, oder `memory-bank-goal` für einen Satz |

Die beiden ergänzen sich, sie konkurrieren nicht. Behalten Sie `/grill-me` für Entscheidungen, aus denen kein Projekt entsteht, etwa einen Architekturstreit, einen Einstellungsplan oder ein Vortragsgerüst. Greifen Sie zu `memory-bank-init`, wenn das, worüber Sie grillen, eine Codebasis ist, die nächste Woche noch wissen muss, was sie ist.

## Den API-Harness installieren

Dieser Abschnitt ist optional. Alles oben funktioniert auch ohne ihn, denn der Harness ergänzt lediglich eine unbeaufsichtigte Schleife, die einen Agenten über die API steuert, statt dass Sie selbst tippen. Lassen Sie ihn weg, wenn Codex, Claude Code oder ein anderer Agent das bereits für Sie erledigt.

Der API-Harness ist kontoweit, weil er jedes Projekt steuern kann, das dieser Memory-Bank-Struktur folgt. Er braucht Python 3 und sonst nichts.

```bash
mkdir -p ~/.local/bin
cp /path/to/skills/harness/tackle-memory-bank-api-loop ~/.local/bin/
chmod +x ~/.local/bin/tackle-memory-bank-api-loop
```

Die Befehle unten rufen `tackle-memory-bank-api-loop` über den Namen auf; dafür muss `~/.local/bin` in Ihrem `PATH` liegen. Wenn `command -v tackle-memory-bank-api-loop` nichts ausgibt, fügen Sie diese Zeile Ihrem Shell-Profil hinzu:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Ein ausführbarer Lauf übergibt modellgenerierte Befehle an eine nicht sandboxierte Shell auf dem Host. Deshalb startet der Harness erst nach der ausdrücklichen Bestätigung mit `ALLOW_UNSANDBOXED_SHELL=1` oder `--allow-unsandboxed-shell`. Das ist eine Risikobestätigung, keine Isolation: Befehle können Host-Dateien und andere Prozesse lesen und das Netzwerk nutzen. Führen Sie den Harness in einer wegwerfbaren Sandbox und nur gegen ein wiederherstellbares Repository aus.

Shell-Befehle erhalten nur eine minimale Umgebung; Provider-Zugangsdaten werden nicht hineinkopiert. Zusätzliche Projektvariablen werden mit `TOOL_ENV_ALLOW=NAME,OTHER_NAME` ausdrücklich freigegeben. Das verringert versehentliche Offenlegung, macht die Host-Shell aber nicht sicher. `ALLOW_DANGEROUS_COMMANDS=1` deaktiviert lediglich eine kurze, umgehbare Befehls-Sperrliste.

Eine Zeile ausführen:

```bash
ALLOW_UNSANDBOXED_SHELL=1 LLM_MODEL=gpt-5.6 OPENAI_API_KEY=... MAX_RUNS=1 tackle-memory-bank-api-loop .
```

Eine Schleife ausführen:

```bash
ALLOW_UNSANDBOXED_SHELL=1 LLM_MODEL=gpt-5.6 OPENAI_API_KEY=... MAX_RUNS=5 tackle-memory-bank-api-loop .
```

Einen OpenAI-kompatiblen Provider verwenden:

```bash
LLM_API_BASE=https://openrouter.ai/api/v1 \
LLM_API_KEY=... \
LLM_MODEL=openai/gpt-5.6 \
ALLOW_UNSANDBOXED_SHELL=1 \
MAX_RUNS=1 \
tackle-memory-bank-api-loop .
```

Einen lokalen OpenAI-kompatiblen Server verwenden:

```bash
LLM_API_BASE=http://localhost:1234/v1 \
LLM_MODEL=local-model-name \
ALLOW_UNSANDBOXED_SHELL=1 \
MAX_RUNS=1 \
tackle-memory-bank-api-loop .
```

Anthropic (Claude) statt des OpenAI-kompatiblen Wegs verwenden:

```bash
LLM_PROVIDER=anthropic \
LLM_MODEL=claude-opus-5 \
ANTHROPIC_API_KEY=... \
ALLOW_UNSANDBOXED_SHELL=1 \
MAX_RUNS=1 \
tackle-memory-bank-api-loop .
```

Der Harness bettet die Aufgabenanweisung in seinen API-Prompt ein. Er ruft nicht die Codex CLI auf und benötigt die externe Prompt-Datei zur Laufzeit nicht. Die Prompt-Datei bleibt als menschenlesbare, mit der eingebetteten Anweisung synchronisierte Kopie im Repository; sie wird nicht in ein Codex-Prompt-Verzeichnis installiert.

Modellnamen ändern sich. Die Beispiele verwenden den aktuellen `gpt-5.6`-Family-Alias und `claude-opus-5`; prüfen Sie für echte Läufe den offiziellen [OpenAI model catalog](https://developers.openai.com/api/docs/models) und [Anthropic model catalog](https://platform.claude.com/docs/en/about-claude/models/overview).

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

Der Harness stoppt absichtlich früh, und sein Exit-Code sagt warum. `3` bis `7` sind normale Stoppbedingungen und keine Fehler. `4` bedeutet etwa, dass der Worktree vor dem Lauf nicht sauber war, und `6`, dass der Agent ohne Commit fertig wurde. `11` bedeutet, dass keine `status-<LANE><NN>.md`-Dateien gefunden wurden, was meist heißt, dass die Memory Bank noch nicht ausgefüllt ist. Die vollständige Tabelle steht im [Ausführungs-Harness](docs/EXECUTION_de.md#exit-codes).

## Was der Harness ist

Für normale Projektarbeit ist `tackle-memory-bank-api-loop` ein Ausführungs-Harness: Er führt wiederholt einen Agenten gegen ein Repository aus, gibt ihm shell-Zugriff über ein JSON-Befehlsprotokoll und prüft zwischen den Läufen den git-Zustand. Das Ziel muss genau die git-worktree-root sein, die Historie muss ohne Umschreiben voranschreiten, und pro Lauf muss genau eine vorhandene ausführbare Zeile abgeschlossen oder blockiert werden. Separate Commits für Milestone-Review-Korrekturen im selben Lauf bleiben erlaubt.

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
