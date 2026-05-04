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
- `memory-bank/status.md` hält fest, ob Harness-bezogene Zeilen pending, complete, blocked oder cancelled sind.

## Agenten-Ausführungs-Harness

Das enthaltene [.local/bin/tackle-memory-bank-api-loop](../.local/bin/tackle-memory-bank-api-loop) ist ein Agenten-Ausführungs-Harness.

Er:

- ruft eine OpenAI-kompatible chat-completions API auf,
- bettet die memory-bank-Aufgabenanweisung direkt in den API-Aufruf ein,
- gibt dem Modell ein shell-Befehlsprotokoll,
- stoppt, wenn keine ausführbaren Zeilen mehr übrig sind,
- stoppt, wenn blocked-Zeilen existieren,
- prüft vor jedem Lauf auf einen sauberen git worktree,
- verlangt vom Modell, seine Arbeit zu committen,
- stoppt, wenn das Modell uncommitted changes zurücklässt,
- stoppt, wenn das Modell keinen commit erzeugt,
- begrenzt die Anzahl der Schleifendurchläufe.

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
