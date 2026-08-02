# Un harness d’ingénierie minimal

Les agents de code travaillent mieux quand un projet sait s'expliquer — ce qu'il est, ce qui est fait, ce qui vient ensuite. La façon habituelle d'y arriver est d'adopter un système : un CLI, un scaffold, une série de commandes slash, un dossier d'artefacts générés. Six mois plus tard, vous maintenez les fichiers de ce système autant que votre propre code, et votre projet vit dans ses conventions plutôt que dans les vôtres.

Ce dépôt fait le pari inverse. Cinq ou six fichiers markdown, copiés dans votre projet, qui vous appartiennent entièrement. Aucun CLI à installer, aucun vocabulaire à apprendre, rien d'obligatoire. Supprimez-en n'importe lequel le jour où il cesse de mériter sa place.

**Rien ne s'exécute ici.** Ce dépôt est un point de départ dont vous copiez le contenu *vers l'extérieur* — `template/` dans votre projet, `harness/` éventuellement dans votre répertoire personnel. Ensuite votre projet n'a aucune dépendance envers ce dépôt ni aucun lien de retour. C'est justement l'objectif : ce que vous obtenez vous appartient.

Votre projet finit par ressembler à ceci :

```text
your-project/
├── AGENTS.md              ce qu'un agent doit lire en premier
├── memory-bank/           ce qui est vrai maintenant
│   ├── product.md         ce que c'est, et ce que ce n'est pas
│   ├── architecture.md    structure, flux de données, frontières
│   ├── tech-stack.md      commandes, dépendances, vérification
│   ├── milestone.md       milestones et critères d'acceptation
│   └── status-M01.md      un fichier par milestone, une ligne par tâche
└── evolution/             pourquoi la direction a changé
```

Dans tout ce document, **harness** désigne une commande reproductible qui prouve que quelque chose fonctionne — votre suite de tests, un job CI, un script. Votre projet définit le sien dans `tech-stack.md`. Ce dépôt fournit en plus un harness optionnel : une boucle API qui pilote un agent à travers la memory bank sans surveillance.

Autres versions linguistiques: [🇬🇧 English](README.md) · [🇨🇳 中文](README_cn.md) · [🇯🇵 日本語](README_ja.md) · [🇩🇪 Deutsch](README_de.md) · [🇪🇸 Español](README_es.md).

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

## À quoi ressemble une memory bank remplie

Le modèle contient des placeholders. Voici la même memory bank remplie pour un petit service de boutique, pour voir la destination avant l'itinéraire.

`memory-bank/product.md` commence par `[project-name] is [one or two sentences describing the project]` et devient :

```markdown
`cartsvc` is the shopping cart and checkout service behind the storefront.
It owns cart state, pricing, and the handoff to payments.
```

`memory-bank/milestone.md` décide de l'organisation de tout le reste : il nomme les voies et dit ce que chacune couvre.

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

Ensuite `memory-bank/status-S01.md` porte les lignes de ce milestone :

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

Avant de faire confiance à tout cela, donnez à l’agent quelque chose à vérifier. Remplissez le tableau **Execution harnesses** de `memory-bank/tech-stack.md` avec la commande qui prouve que votre projet fonctionne — `make test`, `npm test`, un script, ce que vous lancez déjà — et ce que sa réussite prouve. Une ligne ne devrait pas passer à `[+]` avant que cette commande soit passée. Sans cela, « ne marquer une ligne terminée qu’après vérification » n’a aucun référent et l’agent décide seul de ce que vérifier veut dire.

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

**Choisir ses voies.** Une voie est un axe de travail durable, pas un milestone ni un sprint. Classez par domaine — la partie du produit à laquelle un changement appartient — plutôt que par équipe, priorité ou date, car les domaines survivent aux trois. Commencez avec `M` seul ; détachez une lettre la première fois qu'un domaine a assez de travail pour noyer le reste, ou quand il lui faut son propre rythme de revue. Deux ou trois voies est un régime permanent normal, et un projet peut tenir longtemps avec une seule.

Sous-découper se corrige à peu de frais : ouvrez une nouvelle lettre et mettez-y le travail à venir. Sur-découper non, car les identifiants ne sont jamais réutilisés ni renommés une fois le fichier créé — une voie que vous regrettez reste dans l'arbre pour toujours. Dans le doute, laissez dans `M`.

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

Il s’invoque, il n’est pas permanent. Quel que soit votre agent, la requête qui lance une exécution est le même bloc — elle nomme le fichier, l’ordre et la politique de commit :

```text
Using GOAL.md, execute this loop.

STATUS_ORDER: M01 -> S01 -> A01?
COMMIT_POLICY: task
```

La façon d’envoyer ce bloc diffère, car `/goal` n’est pas la même commande dans tous les agents. Reportez-vous à la section correspondant au vôtre.

#### Si vous utilisez Claude Code

`/goal` est intégré, et ce **n’est pas** un moyen de lancer une tâche. Il définit une condition d’arrêt — « un objectif que Claude vérifie avant de s’arrêter » — de sorte que la session continue à travailler sur plusieurs tours au lieu de s’arrêter après une réponse.

Il faut donc deux messages. Envoyez le bloc ci-dessus comme un message ordinaire, puis définissez la condition qui décide de la fin de l’exécution :

```text
/goal every row in M01 and S01 is `[+]` and the required verification passes
```

`/goal active` affiche la condition courante et `/goal clear` y met fin par avance. La condition est limitée à 4000 caractères, exige un espace de travail de confiance, et n’est pas disponible lorsque les hooks sont désactivés par les réglages ou par une politique.

Pour rendre le bloc lui-même réutilisable, enregistrez-le comme commande de projet — mais pas sous `.claude/commands/goal.md`, car la commande intégrée occupe ce nom. Appelez-le `.claude/commands/milestones.md` et invoquez-le avec `/milestones`.

#### Si vous utilisez Codex

Il n’y a pas de `/goal` intégré. Les prompts personnalisés sont des fichiers markdown dans `~/.codex/prompts/`, invoqués par leur nom de fichier : vous pouvez donc créer la commande vous-même et lui faire prendre l’ordre en argument. Créez `~/.codex/prompts/goal.md` :

```markdown
---
description: Execute an ordered set of milestones using GOAL.md.
argument-hint: M01 -> S01 -> A01?
---

Using GOAL.md, execute this loop.

STATUS_ORDER: $ARGUMENTS
COMMIT_POLICY: task
```

Un seul message suffit alors à le lancer :

```text
/goal M01 -> S01 -> A01?
```

C’est le même mécanisme que le prompt [tackle-next-memory-bank-todo.md](harness/prompts/tackle-next-memory-bank-todo.md) livré avec le paquet, installé dans le même répertoire.

#### Tout autre agent

Collez le bloc comme une requête ordinaire. Le protocole a seulement besoin que le fichier soit nommé ; rien ne dépend de l’existence d’une commande slash.

`COMMIT_POLICY` compte, et une boucle de goal est une exception délibérée à la règle habituelle. Le temps de l’exécution, c’est toute la règle de commit : `AGENTS.md` a beau dire que chaque ligne de statut est une unité de commit, `COMMIT_POLICY: none` — la valeur par défaut du protocole — signifie aucun commit du tout, et c’est le comportement correct, pas un conflit. Écrivez `task` pour retrouver les commits par ligne. L’ordre de priorité est la demande, puis `GOAL.md`, puis `AGENTS.md` — et seulement pour les commits, et seulement pendant l’exécution.

Un `?` final marque un milestone conditionnel : il est ignoré, pas annulé, quand son déclencheur documenté est absent.

`GOAL.md` ne contient aucun chemin, aucune lettre de voie ni aucune commande propres à un projet. Il les lit depuis `AGENTS.md` et la memory bank, ce qui permet au même fichier de fonctionner tel quel dans tout projet qui le copie.

Rien ne vous oblige à l’utiliser. `/goal` est la commande de votre agent, pas celle de ce harness : apportez votre propre protocole, ou aucun, la memory bank se comporte exactement pareil. `GOAL.md` est fourni parce qu’écrire ce genre de protocole est fastidieux, pas parce que quoi que ce soit ici en dépend. Si vous avez le vôtre, faites pointer dessus les deux mentions de `GOAL.md` — dans `AGENTS.md` et `memory-bank/milestone.md` — ou supprimez-les.

## Installer les trois commandes

Également optionnel. Tout ce qui précède fonctionne en tapant des phrases ordinaires ; ces commandes rendent simplement les trois moments reproductibles et portent l’instruction complète plutôt que votre paraphrase.

| Commande | Quand |
|---|---|
| `/memory-bank-init` | Une fois, sur un projet sans `memory-bank/`. Elle vous interroge, propose un découpage, puis écrit les fichiers. |
| `/memory-bank-next` | Au quotidien. Traiter une ligne, vérifier, committer. |
| `/memory-bank-goal` | Quand vous voulez exécuter plusieurs milestones dans l’ordre. |

`/memory-bank-init` est celle qui change le plus l’expérience : elle pose une question à la fois, assortie d’une réponse recommandée, cherche elle-même tout ce qu’elle peut lire dans le dépôt au lieu de le demander, et n’écrit rien tant que vous n’avez pas approuvé le découpage. Vous ne voyez aucun placeholder entre crochets — la memory bank arrive remplie. (Technique d’entretien adaptée du skill `grilling` de [mattpocock/skills](https://github.com/mattpocock/skills), MIT.)

Les deux agents lisent le même format `SKILL.md`, il n’y a donc qu’une source par commande :

```bash
# Claude Code — as a plugin, updates when this repo ships
/plugin marketplace add tabilet/skills
/plugin install memory-bank

# Claude Code — or as plain files you own and can edit
cp -R /path/to/skills/harness/skills/. ~/.claude/skills/

# Codex
cp -R /path/to/skills/harness/skills/. ~/.codex/skills/
```

Le plugin installe le **générateur**, pas le résultat. Ce qu’il écrit dans votre projet vous appartient, n’est jamais mis à jour depuis ici, et survit à sa désinstallation.

Le skill ne s’appelle délibérément pas `goal` : Claude Code possède un `/goal` intégré qui définit une condition d’arrêt, ce qui est autre chose. Les deux fonctionnent ensemble, voir « Exécuter plusieurs milestones dans l’ordre ».

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

Utiliser Anthropic (Claude) au lieu de la voie compatible OpenAI :

```bash
LLM_PROVIDER=anthropic \
LLM_MODEL=claude-opus-5 \
ANTHROPIC_API_KEY=... \
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
