# Ausführungs-Harness

Ein Ausführungs-Harness (execution harness) ist die wiederholbare Art, ein Projekt unter den Bedingungen auszuführen, die wirklich zählen. Meist ist er ein Programm, Skript, Test-Target, eine Docker-Compose-Datei oder ein CI job.

Markdown führt den Harness nicht aus. Markdown erklärt Menschen und Agenten, wie er gestartet wird, welche Dienste er startet, welche Nachweise er erzeugt und welche Fehler bekannt oder erwartet sind.

## Beispiele

- Ein `make test`-Target, das alle Unit-Tests ausführt.
- Ein `make integration`-Target, das PostgreSQL- und MySQL-Container startet, Datenbanktests ausführt und die Container anschließend stoppt.
- Ein Go-Testpaket, das mit `testcontainers-go` echte Dienste startet.
- Ein Skript, das eine CLI baut, sie mit fixture-Eingaben ausführt und die erzeugte Ausgabe per diff vergleicht.
- Ein CI workflow, der auf jedem pull request dieselben Befehle ausführt.

## Wo er hineinpasst

- `AGENTS.md` listet die wesentlichen Harness-Befehle, die Agenten ausführen sollen.
- `memory-bank/tech-stack.md` dokumentiert Voraussetzungen, Umgebungsvariablen, Docker images, Ports und Befehlsnamen.
- `docs/` enthält ausführlichere Hinweise zu Setup, Teardown und Troubleshooting.
- `memory-bank/milestone.md` kann einen bestandenen Harness als Teil der Akzeptanz definieren.
- `memory-bank/status-<LANE><NN>.md` hält fest, ob Harness-bezogene Zeilen pending, complete, blocked oder cancelled sind.

## Agenten-Ausführungs-Harness

Das enthaltene [harness/tackle-memory-bank-api-loop](../harness/tackle-memory-bank-api-loop) ist ein Agenten-Ausführungs-Harness.

Er:

- ruft eine OpenAI-kompatible chat-completions API auf, oder die Anthropic Messages API bei `LLM_PROVIDER=anthropic`,
- bettet die memory-bank-Aufgabenanweisung direkt in den API-Aufruf ein,
- gibt dem Modell ein shell-Befehlsprotokoll,
- findet jede `memory-bank/status-<LANE><NN>.md`-Lane-Datei und meldet dem Modell die Anzahl ausführbarer und blockierter Zeilen je Lane,
- stoppt, wenn in keiner Lane mehr ausführbare Zeilen übrig sind,
- warnt vor blocked-Zeilen und stoppt für menschliche Prüfung erst, wenn nur noch blocked-Zeilen übrig sind,
- prüft vor jedem Lauf auf einen sauberen git worktree,
- verlangt vom Modell, seine Arbeit zu committen,
- stoppt, wenn das Modell uncommitted changes zurücklässt,
- stoppt, wenn das Modell keinen commit erzeugt,
- begrenzt die Anzahl der Schleifendurchläufe.

### Exit-Codes

Der Harness signalisiert jedes Ergebnis über seinen Exit-Code. Die Codes `3` bis `7` sind normale Stoppbedingungen und keine Abstürze: Die Schleife hat die Kontrolle bewusst an einen Menschen zurückgegeben.

| Code | Bedeutung |
|---|---|
| `0` | Keine ausführbaren Zeilen mehr übrig. Nichts zu tun. |
| `2` | `LLM_MODEL` nicht gesetzt oder `LLM_PROVIDER` ist weder `openai` noch `anthropic`. |
| `3` | Nur noch blockierte Zeilen übrig. Ein Mensch muss sie entsperren. |
| `4` | Der Worktree war vor einem Lauf nicht sauber. Erst committen oder stashen. |
| `5` | Der Agent hat uncommitted changes hinterlassen. |
| `6` | Der Agent hat keinen Commit erzeugt. Verhindert eine Endlosschleife. |
| `7` | `MAX_RUNS` wurde erreicht. |
| `10` | Kein `AGENTS.md` im Ziel-Repository. |
| `11` | Kein `memory-bank/` oder keine `status-<LANE><NN>.md`-Dateien darin. |
| `12` | Der Zielpfad liegt nicht in einem git worktree. |
| `13` | Git `HEAD` konnte nicht gelesen werden. |
| `20` | Die API hat einen HTTP-Fehler zurückgegeben. |
| `21` | Die API war nicht erreichbar. |
| `22` | Die API-Antwort entsprach nicht der erwarteten Form. |
| `30` | Das Modell hat `MAX_TURNS` verbraucht, ohne eine Zeile abzuschließen. |

Die Codes `10` bis `13` bedeuten, dass das Ziel-Repository noch nicht eingerichtet ist. `20` bis `22` sind Provider- oder Netzwerkprobleme, keine Projektprobleme.

## Docker-gestützte Dienste

Für Tests, die Dienste wie MySQL oder PostgreSQL benötigen, sollten kurzlebige Container lokalen Pflichtinstallationen vorgezogen werden.

Typischer Ablauf:

1. Dienstcontainer mit Docker Compose, `testcontainers` oder einem Harness-Skript starten.
2. Warten, bis health checks erfolgreich sind.
3. Integrationstests ausführen.
4. Bei Fehlern Logs sammeln.
5. Container stoppen und entfernen.

So bleiben lokale Entwicklungsmaschinen und CI-Umgebungen näher beieinander.

## Einen Harness dokumentieren

Für jeden Ausführungs-Harness sollte festgehalten werden:

- Befehl,
- Szenario,
- benötigte Dienste,
- Umgebungsvariablen,
- fixture oder seed data,
- erwartete erfolgreiche Ausgabe,
- Artifact- und Log-Speicherorte,
- CI job name,
- bekannte Einschränkungen oder blocked-Zeilen.

Die aktive Befehlsliste gehört in `memory-bank/tech-stack.md`. Längere Betriebsdetails gehören in `docs/`.
