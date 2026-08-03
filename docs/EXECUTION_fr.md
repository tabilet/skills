# Harness d’exécution

Un harness d’exécution (execution harness) est une façon répétable d’exécuter un projet dans les conditions qui comptent. Il s’agit généralement d’un programme, d’un script, d’une cible de test, d’un fichier Docker Compose ou d’un CI job.

Markdown n’exécute pas le harness. Markdown explique aux humains et aux agents comment le lancer, quels services il démarre, quelles preuves il produit et quels échecs sont connus ou attendus.

## Exemples

- Une cible `make test` qui exécute tous les tests unitaires.
- Une cible `make integration` qui démarre des conteneurs PostgreSQL et MySQL, exécute les tests de base de données, puis arrête les conteneurs.
- Un package de tests Go qui utilise `testcontainers-go` pour lancer de vrais services.
- Un script qui construit une CLI, l’exécute avec des entrées fixture, puis compare la sortie générée avec diff.
- Un CI workflow qui exécute les mêmes commandes sur chaque pull request.

## Où il s’insère

- `AGENTS.md` liste les commandes harness essentielles que les agents doivent exécuter.
- `memory-bank/tech-stack.md` consigne les prérequis, variables d’environnement, Docker images, ports et noms de commandes.
- `docs/` contient les notes longues de setup, teardown et troubleshooting.
- `memory-bank/milestone.md` peut intégrer la réussite d’un harness dans les critères d’acceptation.
- `memory-bank/status-<LANE><NN>.md` indique si les lignes liées au harness sont pending, complete, blocked ou cancelled.

## Harness d’exécution d’agent

Le fichier inclus [harness/tackle-memory-bank-api-loop](../harness/tackle-memory-bank-api-loop) est un harness d’exécution d’agent.

Il :

- appelle une API chat-completions compatible OpenAI, ou l’API Anthropic Messages avec `LLM_PROVIDER=anthropic` ;
- intègre directement l’instruction de tâche memory-bank dans l’appel API ;
- fournit au modèle un protocole de commandes shell ;
- découvre chaque fichier de voie `memory-bank/status-<LANE><NN>.md` et indique au modèle le nombre de lignes actionnables et bloquées par voie ;
- s’arrête lorsqu’aucune voie ne contient plus de ligne actionnable ;
- signale les lignes blocked et ne s’arrête pour revue humaine que s’il ne reste que des lignes blocked ;
- vérifie que le git worktree est propre avant chaque exécution ;
- exige que le modèle commit son travail ;
- s’arrête si le modèle laisse des changements non commit ;
- s’arrête si le modèle ne crée aucun commit ;
- limite le nombre d’itérations de boucle.

### Codes de sortie

Le harness signale chaque résultat par son code de sortie. Les codes `3` à `7` sont des conditions d’arrêt normales, pas des plantages : la boucle a délibérément rendu la main à un humain.

| Code | Signification |
|---|---|
| `0` | Il ne reste aucune ligne actionnable. Rien à faire. |
| `2` | `LLM_MODEL` non défini, ou `LLM_PROVIDER` n’est ni `openai` ni `anthropic`. |
| `3` | Il ne reste que des lignes bloquées. Un humain doit les débloquer. |
| `4` | Le worktree n’était pas propre avant l’exécution. Committez ou stashez d’abord. |
| `5` | L’agent a laissé des modifications non commitées. |
| `6` | L’agent n’a créé aucun commit. Évite une boucle à vide. |
| `7` | `MAX_RUNS` a été atteint. |
| `10` | Pas de `AGENTS.md` dans le dépôt cible. |
| `11` | Pas de `memory-bank/`, ou aucun fichier `status-<LANE><NN>.md` dedans. |
| `12` | Le chemin cible n’est pas dans un worktree git. |
| `13` | Impossible de lire le `HEAD` git. |
| `20` | L’API a renvoyé une erreur HTTP. |
| `21` | L’API était injoignable. |
| `22` | La réponse de l’API ne correspondait pas à la forme attendue. |
| `30` | Le modèle a épuisé `MAX_TURNS` sans terminer une ligne. |

Les codes `10` à `13` signifient que le dépôt cible n’est pas encore configuré. Les codes `20` à `22` sont des problèmes de fournisseur ou de réseau, pas de projet.

## Services appuyés par Docker

Pour les tests qui nécessitent des services comme MySQL ou PostgreSQL, privilégiez des conteneurs jetables plutôt que des installations locales obligatoires.

Flux typique :

1. Démarrer les conteneurs de service avec Docker Compose, `testcontainers` ou un script harness.
2. Attendre que les health checks réussissent.
3. Exécuter les tests d’intégration.
4. Collecter les logs en cas d’échec.
5. Arrêter et supprimer les conteneurs.

Cela rapproche les machines de développement locales et les environnements CI.

## Documenter un harness

Pour chaque harness d’exécution, consignez :

- commande ;
- scénario ;
- services requis ;
- variables d’environnement ;
- fixture ou seed data ;
- sortie attendue en cas de réussite ;
- emplacements des artifacts et logs ;
- nom du CI job ;
- limitations connues ou lignes blocked.

La liste active des commandes appartient à `memory-bank/tech-stack.md`. Les détails opérationnels plus longs appartiennent à `docs/`.
