# Un harness d’ingénierie minimal

Ce dépôt est un point de départ copiable pour un système d’exploitation de projet léger, construit autour de :

- `AGENTS.md` comme guide de bootstrap pour les agents.
- `memory-bank/` comme source de vérité actuelle du projet.
- `evolution/` comme historique versionné des changements de direction.
- des harnesses d’exécution comme commandes répétables qui prouvent que le logiciel fonctionne.
- des harnesses d’évaluation de modèle comme évaluations répétables qui mesurent le comportement assisté par modèle.

L’objectif n’est pas d’augmenter le volume de documentation. L’objectif est de donner aux humains et aux agents le même manuel d’exploitation compact, puis de relier ce manuel à des harnesses exécutables.

## Démarrage

**Pour utiliser la memory bank, il vous faut `git`, et rien d’autre.** La memory bank est du markdown ordinaire : le travail quotidien — demander à un agent comme Codex ou Claude Code de traiter le prochain élément en attente — ne demande aucun runtime.

**Python 3 ne sert qu’au harness API optionnel**, la boucle autonome décrite dans [Installer le harness API](#installer-le-harness-api). Il n’utilise que la bibliothèque standard, il n’y a donc rien à installer avec `pip`. Ignorez-le complètement si vous pilotez déjà la memory bank depuis un agent que vous utilisez.

Les instructions pour un projet existant, plus bas, utilisent aussi [ripgrep](https://github.com/BurntSushi/ripgrep) (`rg`) pour l’inventaire initial.

Clonez ce dépôt une fois. Chaque commande `cp` ci-dessous désigne votre clone par `/path/to/skills` :

```bash
git clone https://github.com/tabilet/skills.git
cd skills
```

Rien ne s’exécute depuis le clone lui-même. Vous en copiez des fichiers : `template/` dans un projet, `harness/` dans votre répertoire personnel.

## Ce que contient ce dépôt

Fichiers d’exemple au niveau du projet :

- [template/AGENTS.md](template/AGENTS.md)
- [template/GOAL.md](template/GOAL.md) — le protocole d’exécution multi-milestones
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
5. `memory-bank/status-M01.md` : définir les premières lignes actionnables. Voir plus bas « À quoi ressemble un fichier de statut rempli » — les backticks autour des marqueurs sont déterminants.
6. `evolution/prompt-v1.md` : consigner la direction initiale.
7. `evolution/result-v1.md` : consigner l’état de départ actuel.
8. `AGENTS.md` : remplacer les placeholders par les commandes et règles propres au projet.

Gardez `README.md` simple et orienté utilisateur. Placez les références longues dans `docs/`.

### Brancher votre agent

`AGENTS.md` est un [standard ouvert multi-éditeurs](https://agents.md) porté par l’Agentic AI Foundation. La plupart des agents de code le lisent sans aucune configuration : Codex, Cursor, Gemini CLI, GitHub Copilot, Devin, Windsurf, Jules, Junie, Zed, Aider, VS Code, Warp, goose, opencode, Amp, entre autres.

Aucun fichier propre à un éditeur n’est livré dans `template/`. Si votre agent lit un autre nom de fichier, reliez-le à `AGENTS.md` en une ligne plutôt que de maintenir une seconde copie qui divergera :

| Agent | Passerelle |
|---|---|
| Tout agent de la liste ci-dessus | Rien à faire |
| Claude Code | `ln -s AGENTS.md CLAUDE.md`, ou un `CLAUDE.md` contenant `@AGENTS.md` |
| Tout autre outil lisant son propre fichier | Symlink ou import vers `AGENTS.md`, de la même façon |

Sous Windows, les symlinks demandent des droits Administrateur ou le mode développeur : préférez-y la forme import.

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

Il y a trois façons d’exécuter du travail sur la memory bank, toutes optionnelles — la memory bank est du markdown ordinaire et fonctionne seule :

| Façon d’exécuter | Portée | Nécessite |
|---|---|---|
| Taper une demande à votre agent | Une ligne à la fois, vous dans la boucle | Rien |
| [Le harness API](#installer-le-harness-api) | Une ligne par exécution, sans surveillance | Python 3 |
| [Une boucle de goal](#exécuter-plusieurs-milestones-dans-lordre) | Plusieurs milestones dans l’ordre | Une commande `/goal` |

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

### Voies d’ID de statut

Les fichiers de statut sont nommés `memory-bank/status-<LANE><NN>.md`. La lettre de voie classe le travail et le nombre s’écrit sur deux chiffres avec un zéro initial : les milestones de comptabilité deviennent `status-A01.md` et `status-A02.md`, ceux de la boutique `status-S01.md`. `M` est la voie par défaut pour le travail qui n’entre dans aucune voie de domaine. Une voie contient au plus 99 fichiers ; quand elle est pleine, ouvrez une nouvelle lettre au lieu d’ajouter un troisième chiffre. `memory-bank/milestone.md` consigne le sens de chaque lettre et interdit de réutiliser un identifiant.

Les lignes de statut utilisent ces marqueurs :

| Symbole | Signification |
|---|---|
| `[ ]` | En attente |
| `[+]` | Terminé |
| `[~]` | En cours |
| `[!]` | Bloqué |
| `[X]` | Annulé |

### Exécuter plusieurs milestones dans l’ordre

Le flux ci-dessus avance une ligne à la fois. Pour traiter plusieurs milestones dans un ordre défini, [GOAL.md](template/GOAL.md) est un protocole possible pour cela : il réconcilie les dépendances avant chaque milestone, réconcilie les milestones en aval de celui qui vient de se clore, et s’arrête au lieu de deviner quand une décision ou une autorisation manque.

Il s’invoque, il n’est pas permanent. Codex et Claude Code proposent tous deux une commande `/goal` — celle de Claude Code continue de travailler d’un tour à l’autre jusqu’à ce que la condition du goal soit remplie — et la demande nomme le fichier et l’ordre :

```text
/goal
Using GOAL.md, execute this loop.

STATUS_ORDER: M01 -> S01 -> A01?
COMMIT_POLICY: task
```

`COMMIT_POLICY` compte, et une boucle de goal est une exception délibérée à la règle habituelle. Le temps de l’exécution, c’est toute la règle de commit : `AGENTS.md` a beau dire que chaque ligne de statut est une unité de commit, `COMMIT_POLICY: none` — la valeur par défaut du protocole — signifie aucun commit du tout, et c’est le comportement correct, pas un conflit. Écrivez `task` pour retrouver les commits par ligne. L’ordre de priorité est la demande, puis `GOAL.md`, puis `AGENTS.md` — et seulement pour les commits, et seulement pendant l’exécution.

Un `?` final marque un milestone conditionnel : il est ignoré, pas annulé, quand son déclencheur documenté est absent.

`GOAL.md` ne contient aucun chemin, aucune lettre de voie ni aucune commande propres à un projet. Il les lit depuis `AGENTS.md` et la memory bank, ce qui permet au même fichier de fonctionner tel quel dans tout projet qui le copie.

Rien ne vous oblige à l’utiliser. `/goal` est la commande de votre agent, pas celle de ce harness : apportez votre propre protocole, ou aucun, la memory bank se comporte exactement pareil. `GOAL.md` est fourni parce qu’écrire ce genre de protocole est fastidieux, pas parce que quoi que ce soit ici en dépend. Si vous avez le vôtre, faites pointer dessus les deux mentions de `GOAL.md` — dans `AGENTS.md` et `memory-bank/milestone.md` — ou supprimez-les.

### À quoi ressemble un fichier de statut rempli

Les modèles contiennent des placeholders. Rempli pour un petit service de boutique, `memory-bank/status-S01.md` ressemble à ceci :

```markdown
# Status S01 - Cart And Checkout

| Item | State | Notes |
|---|---|---|
| Add POST /cart endpoint | `[+]` | Verified by tests/cart_test.py. |
| Cart total calculation | `[~]` | Rounding rules still open. |
| Wire cart to checkout | `[ ]` | Blocked on the A02 payment contract. |
| Guest checkout | `[X]` | Cancelled; accounts required at launch. |
```

**Les backticks autour de chaque marqueur sont obligatoires.** Le harness reconnaît `` `[ ]` ``, pas `[ ]`. Une ligne écrite `| Item | [ ] | Notes |` est ignorée en silence : le harness affiche « No actionable memory-bank rows remain » et se termine avec succès, comme si le travail était fini.

Le même remplacement de placeholders s’applique au reste de la memory bank. `memory-bank/product.md` commence par `[project-name] is [one or two sentences describing the project]` et devient :

```markdown
`cartsvc` is the shopping cart and checkout service behind the storefront.
It owns cart state, pricing, and the handoff to payments.
```


## Installer le harness API

Cette section est optionnelle. Tout ce qui précède fonctionne sans elle : le harness ajoute seulement une boucle autonome qui pilote un agent via l’API au lieu que vous tapiez vous-même. Ignorez-la si Codex, Claude Code ou un autre agent le fait déjà pour vous.

Le harness API est au niveau du compte, car il peut piloter tout projet qui suit cette forme de memory bank. Il nécessite Python 3 et rien d’autre.

```bash
mkdir -p ~/.local/bin ~/.codex/prompts
cp /path/to/skills/harness/tackle-memory-bank-api-loop ~/.local/bin/
cp /path/to/skills/harness/prompts/tackle-next-memory-bank-todo.md ~/.codex/prompts/
chmod +x ~/.local/bin/tackle-memory-bank-api-loop
```

Les commandes ci-dessous appellent `tackle-memory-bank-api-loop` par son nom, ce qui exige que `~/.local/bin` soit dans votre `PATH`. Si `command -v tackle-memory-bank-api-loop` n’affiche rien, ajoutez cette ligne à votre profil shell :

```bash
export PATH="$HOME/.local/bin:$PATH"
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

### Première exécution

Une exécution affiche d’abord le dépôt, le fournisseur, le modèle et le point d’accès API, puis traite une ligne :

```text
Repo: /path/to/your-project
Provider: anthropic
Model: claude-opus-5
API: https://api.anthropic.com/v1/messages
Run 1/1: asking LLM to tackle one row.
  LLM turn 1/60
  shell: sed -n '1,120p' AGENTS.md  # Read the bootstrap guide.
```

Le harness s’arrête tôt volontairement, et son code de sortie en donne la raison. `3` à `7` sont des arrêts normaux, pas des échecs : `4` signifie que le worktree n’était pas propre avant l’exécution, et `6` que l’agent a terminé sans commit. `11` signifie qu’aucun fichier `status-<LANE><NN>.md` n’a été trouvé, ce qui veut généralement dire que la memory bank n’a pas encore été remplie. Le tableau complet se trouve dans [Harness d’exécution](docs/EXECUTION_fr.md#codes-de-sortie).

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
