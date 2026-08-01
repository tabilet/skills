# Un harness d’ingénierie minimal

Ce dépôt est un point de départ copiable pour un système d’exploitation de projet léger, construit autour de :

- `AGENTS.md` comme guide de bootstrap pour les agents.
- `memory-bank/` comme source de vérité actuelle du projet.
- `evolution/` comme historique versionné des changements de direction.
- des harnesses d’exécution comme commandes répétables qui prouvent que le logiciel fonctionne.
- des harnesses d’évaluation de modèle comme évaluations répétables qui mesurent le comportement assisté par modèle.

L’objectif n’est pas d’augmenter le volume de documentation. L’objectif est de donner aux humains et aux agents le même manuel d’exploitation compact, puis de relier ce manuel à des harnesses exécutables.

## Ce que contient ce dépôt

Fichiers d’exemple au niveau du projet :

- [template/AGENTS.md](template/AGENTS.md)
- [template/memory-bank/product.md](template/memory-bank/product.md)
- [template/memory-bank/architecture.md](template/memory-bank/architecture.md)
- [template/memory-bank/tech-stack.md](template/memory-bank/tech-stack.md)
- [template/memory-bank/milestone.md](template/memory-bank/milestone.md)
- [template/memory-bank/status-M01.md](template/memory-bank/status-M01.md)
- [template/evolution/prompt-v1.md](template/evolution/prompt-v1.md)
- [template/evolution/result-v1.md](template/evolution/result-v1.md)

Fichiers d’exemple au niveau du compte utilisateur :

- [harness/tackle-memory-bank-api-loop](harness/tackle-memory-bank-api-loop)
- [harness/prompts/tackle-next-memory-bank-todo.md](harness/prompts/tackle-next-memory-bank-todo.md)

Références harness :

- [Harness d’exécution](docs/EXECUTION_fr.md)
- [Harness d’évaluation de modèle](docs/MODEL_EVAL_fr.md)

## Configurer un nouveau projet

### Manuellement

Depuis la racine d’un nouveau projet :

```bash
cp -R /path/to/skills/template/. .
mkdir -p docs
```

Modifiez ensuite les fichiers copiés dans cet ordre :

1. `memory-bank/product.md` : définir ce que le projet est et n’est pas.
2. `memory-bank/architecture.md` : définir le layout, le flux de données et les frontières.
3. `memory-bank/tech-stack.md` : définir les commandes, dépendances et harnesses.
4. `memory-bank/milestone.md` : définir le premier milestone.
5. `memory-bank/status-M01.md` : définir les premières lignes actionnables.
6. `evolution/prompt-v1.md` : consigner la direction initiale.
7. `evolution/result-v1.md` : consigner l’état de départ actuel.
8. `AGENTS.md` : remplacer les placeholders par les commandes et règles propres au projet.

Gardez `README.md` simple et orienté utilisateur. Placez les références longues dans `docs/`.

### Avec l’aide d’un agent IA

Pour un nouveau projet, vous pouvez utiliser les fichiers d’exemple comme structure initiale et demander à un agent IA de les remplir après avoir décrit le produit.

Avertissement : copier ces fichiers par-dessus un projet existant peut écraser des fichiers déjà présents sur disque. Faites d’abord une sauvegarde ou committez votre travail actuel.

Depuis la racine du nouveau projet :

```bash
cp -R /path/to/skills/template/. .
mkdir -p docs
```

Discutez ensuite avec l’agent jusqu’à ce que le produit, les utilisateurs, les frontières, les commandes et le premier milestone soient clairs. Demandez-lui de remplir :

- `AGENTS.md`
- `memory-bank/product.md`
- `memory-bank/architecture.md`
- `memory-bank/tech-stack.md`
- `memory-bank/milestone.md`
- `memory-bank/status-M01.md`
- `evolution/prompt-v1.md`
- `evolution/result-v1.md`

Exemple de prompt :

```text
Read the sample AGENTS.md, memory-bank/*, and evolution/* files. Based on our
discussion of this new project, replace the placeholders with accurate project
content. Keep README user-facing, put long-form references in docs/, define the status
ID lanes in memory-bank/milestone.md, and make memory-bank/status-M01.md contain
the first actionable milestone rows.
```

## Configurer un projet existant

### Manuellement

Pour un projet existant, lire avant d’écrire :

```bash
find . -name '*.md' -print | sort
rg -n "TODO|FIXME|roadmap|architecture|security|deploy|test|release" .
rg --files
```

Ensuite :

1. Lire le README racine, les guides d’agent, docs, README de packages et commentaires des principaux packages.
2. Copier `template/` depuis ce dépôt.
3. Remplir la memory bank à partir de ce que le projet dit déjà, pas depuis une réécriture imaginée.
4. Déplacer les références longues et stables dans `docs/`.
5. Convertir le contenu roadmap/status dupliqué vers `memory-bank/milestone.md` et `memory-bank/status-<LANE><NN>.md`.
6. Garder les lacunes connues visibles dans `status-<LANE><NN>.md` au lieu de les cacher.

### Avec l’aide d’un agent IA

Pour un projet existant, l’agent peut faire l’inventaire et le premier brouillon de memory bank. Cela fonctionne le mieux quand le projet dispose déjà de README utiles, docs, commentaires de packages, tests ou fichiers CI.

Avertissement : copier ces fichiers d’exemple dans un projet existant peut écraser des `AGENTS.md`, `memory-bank/` ou `evolution/` existants. Committez d’abord, faites une sauvegarde ou copiez les exemples dans un emplacement temporaire avant de demander à l’agent de les fusionner.

Depuis la racine du projet existant :

```bash
cp -R /path/to/skills/template/. .
mkdir -p docs
```

Demandez ensuite à l’agent de lire le projet avant d’écrire :

```text
Read the existing README, docs, package README files, tests, build files, and
major source directories. Use that actual project content to fill in AGENTS.md,
memory-bank/*, and evolution/*. Preserve useful existing documentation by moving
long-form references into docs/. Keep known gaps visible in the matching
memory-bank/status-<LANE><NN>.md file.
Do not invent product direction that is not supported by the existing project.
```

L’agent doit :

1. inventorier le markdown existant et le layout du code source.
2. identifier les commandes, dépendances, tests et harnesses.
3. remplir la memory bank depuis la réalité actuelle du projet.
4. déplacer ou résumer les références longues dans `docs/`.
5. garder `README.md` simple et orienté utilisateur.
6. laisser les lacunes non résolues comme lignes pending ou blocked dans `memory-bank/status-<LANE><NN>.md`.

## Utiliser la Memory Bank

Avec un agent comme Codex ou Claude Code, le workflow côté utilisateur peut être aussi simple que de taper :

```text
tackle next pending item in memory bank
```

L’agent doit trouver la prochaine ligne actionnable dans `memory-bank/status-<LANE><NN>.md`, terminer cette tâche, exécuter la vérification requise, mettre à jour la memory bank et créer un git commit au périmètre clair. Si cette ligne est le dernier élément ouvert d’un milestone, l’agent doit lancer la revue de milestone depuis `memory-bank/milestone.md` avant de continuer. Pendant cette revue, il doit aussi décider si `evolution/` a besoin d’une nouvelle version parce que la direction produit, la frontière d’architecture, la cible du milestone ou la direction du contrat public/privé a changé matériellement.

Sous la surface, le workflow normal de l’agent est :

1. Lire `AGENTS.md`.
2. Lire les fichiers memory bank dans l’ordre indiqué par `AGENTS.md`.
3. Traiter exactement une tâche ou ligne de statut au périmètre clair.
4. Mettre à jour le fichier memory-bank correspondant si le scope, l’architecture, les outils, l’acceptance du milestone ou le statut ont changé.
5. Marquer une ligne `[+]` seulement après réussite de la vérification.
6. Committer la ligne comme unité au périmètre clair.
7. Si un milestone devient complet, exécuter la procédure de revue de milestone dans `memory-bank/milestone.md` avant de continuer.
8. Vérifier `evolution/` et ajouter une nouvelle version seulement si la revue trouve un vrai changement de direction, frontière, milestone ou contrat.

Les fichiers de statut sont nommés `memory-bank/status-<LANE><NN>.md`. La lettre de voie classe le travail et le nombre s’écrit sur deux chiffres avec un zéro initial : les milestones de comptabilité deviennent `status-A01.md` et `status-A02.md`, ceux de la boutique `status-S01.md`. `M` est la voie par défaut pour le travail qui n’entre dans aucune voie de domaine. Une voie contient au plus 99 fichiers ; quand elle est pleine, ouvrez une nouvelle lettre au lieu d’ajouter un troisième chiffre. `memory-bank/milestone.md` consigne le sens de chaque lettre et interdit de réutiliser un identifiant.

Les lignes de statut utilisent ces marqueurs :

| Symbole | Signification |
|---|---|
| `[ ]` | En attente |
| `[+]` | Terminé |
| `[~]` | En cours |
| `[!]` | Bloqué |
| `[X]` | Annulé |

## Installer le harness API

Le harness API est au niveau du compte, car il peut piloter tout projet qui suit cette forme de memory bank.

```bash
mkdir -p ~/.local/bin ~/.codex/prompts
cp /path/to/skills/harness/tackle-memory-bank-api-loop ~/.local/bin/
cp /path/to/skills/harness/prompts/tackle-next-memory-bank-todo.md ~/.codex/prompts/
chmod +x ~/.local/bin/tackle-memory-bank-api-loop
```

Exécuter une ligne :

```bash
LLM_MODEL=gpt-5.5 OPENAI_API_KEY=... MAX_RUNS=1 tackle-memory-bank-api-loop .
```

Exécuter une boucle :

```bash
LLM_MODEL=gpt-5.5 OPENAI_API_KEY=... MAX_RUNS=5 tackle-memory-bank-api-loop .
```

Utiliser un fournisseur compatible OpenAI :

```bash
LLM_API_BASE=https://openrouter.ai/api/v1 \
LLM_API_KEY=... \
LLM_MODEL=openai/gpt-5.5 \
MAX_RUNS=1 \
tackle-memory-bank-api-loop .
```

Utiliser un serveur local compatible OpenAI :

```bash
LLM_API_BASE=http://localhost:1234/v1 \
LLM_MODEL=local-model-name \
MAX_RUNS=1 \
tackle-memory-bank-api-loop .
```

Le harness intègre l’instruction de tâche dans son prompt API. Il n’appelle pas la Codex CLI et ne nécessite pas le fichier de prompt externe à l’exécution. Le fichier de prompt est inclus comme référence réutilisable pour les humains et les agents.

## Ce qu’est le harness

Pour le travail projet normal, `tackle-memory-bank-api-loop` est un harness d’exécution : il lance de façon répétée un agent contre un dépôt, lui donne un accès shell via un protocole de commandes contrôlé et vérifie l’état git entre les exécutions.

Il découvre chaque fichier `memory-bank/status-<LANE><NN>.md`, indique combien de lignes actionnables et bloquées contient chaque voie, et laisse l’agent choisir la ligne suivante selon le sens des voies et la priorité des milestones. Une ligne bloquée dans une voie n’arrête pas le travail dans les autres ; la boucle ne s’arrête pour revue humaine que lorsqu’il ne reste que des lignes bloquées.

Il ne devient une partie d’un harness d’évaluation de modèle que lorsque vous notez les résultats entre modèles, prompts, pass rates, review findings, cost, latency ou regressions.

Lire la suite :

- [Harness d’exécution](docs/EXECUTION_fr.md)
- [Harness d’évaluation de modèle](docs/MODEL_EVAL_fr.md)

## Règles de maintenance

- Garder `AGENTS.md` court.
- Garder le `README.md` du projet orienté utilisateur.
- Mettre les longues explications dans `docs/`.
- Mettre la vérité active dans `memory-bank/`.
- Mettre les snapshots historiques de direction dans `evolution/`.
- Mettre à jour la memory dans le même commit que le code ou les docs qu’elle décrit.
- Ajouter une nouvelle version evolution seulement pour un vrai changement de direction.
- Supprimer les docs dupliquées une fois le contenu utile fusionné.
