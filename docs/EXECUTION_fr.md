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
- `memory-bank/status.md` indique si les lignes liées au harness sont pending, complete, blocked ou cancelled.

## Harness d’exécution d’agent

Le fichier inclus [.local/bin/tackle-memory-bank-api-loop](../.local/bin/tackle-memory-bank-api-loop) est un harness d’exécution d’agent.

Il :

- appelle une API chat-completions compatible OpenAI ;
- intègre directement l’instruction de tâche memory-bank dans l’appel API ;
- fournit au modèle un protocole de commandes shell ;
- s’arrête lorsqu’il ne reste plus de ligne actionnable ;
- s’arrête si des lignes blocked existent ;
- vérifie que le git worktree est propre avant chaque exécution ;
- exige que le modèle commit son travail ;
- s’arrête si le modèle laisse des changements non commit ;
- s’arrête si le modèle ne crée aucun commit ;
- limite le nombre d’itérations de boucle.

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
