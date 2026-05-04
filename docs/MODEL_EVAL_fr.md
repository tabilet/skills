# Harness d’évaluation de modèle

Un harness d’évaluation de modèle (model eval harness) est une façon répétable de mesurer un comportement assisté par modèle. Il est utile lorsqu’un projet dépend de prompts, d’agents, de classificateurs, de retrieval, de ranking, de génération, de réparation de code, de résumé ou de tout workflow où la qualité du modèle compte et où les tests logiciels ordinaires ne suffisent pas.

Un harness d’exécution demande : le logiciel s’est-il exécuté correctement ?

Un harness d’évaluation de modèle demande : le comportement du modèle s’est-il amélioré, dégradé ou maintenu sur des tâches représentatives ?

## Exemples

- Un dataset de requêtes utilisateur, de réponses attendues et de rubriques de notation.
- Une suite de régression de prompts qui compare anciens et nouveaux prompts.
- Une exécution baseline-vs-candidate qui mesure accuracy, pass rate, refusal quality, latency et cost.
- Une code-repair eval où les patches générés sont construits et testés dans des sandboxes.
- Une retrieval eval qui mesure si les bons documents ont été sélectionnés.
- Un rapport listant régressions, améliorations et résidus non résolus.

## Où il s’insère

- `memory-bank/product.md` indique quels comportements assistés par modèle comptent pour le produit.
- `memory-bank/architecture.md` consigne où vivent prompts, datasets, graders et reports.
- `memory-bank/tech-stack.md` consigne les fournisseurs de modèles, runners locaux, commandes d’eval, variables d’environnement, contrôles de coût et identifiants requis.
- `memory-bank/milestone.md` peut intégrer un score d’eval ou une revue de régression dans les critères d’acceptation.
- `evolution/` enregistre les changements majeurs de direction sur les prompts, modèles, architectures ou benchmarks.

## Transformer l’API Loop en eval

L’API loop inclus ne devient pas automatiquement un harness d’évaluation de modèle. Il en fait partie lorsque vous exécutez des comparaisons contrôlées et consignez les résultats.

Mesures utiles :

- nom du modèle ;
- version du prompt ;
- dataset ou todo set ;
- pass/fail ;
- nombre d’itérations de boucle ;
- résultats de tests ;
- résultats d’analyse statique ;
- constats de review ;
- acceptation humaine ;
- coût ;
- latence ;
- régressions introduites ;
- échecs résiduels.

## Règles de promotion

Avant de promouvoir un nouveau modèle, prompt ou workflow d’agent, définissez :

- modèle et prompt baseline ;
- modèle et prompt candidate ;
- dataset ou task set ;
- métrique principale ;
- budget de régression autorisé ;
- checks déterministes requis ;
- exigences de review humain ;
- emplacement du rapport.

La règle de promotion doit être assez explicite pour qu’un reviewer puisse dire pourquoi le candidate a réussi ou échoué.

## Rapports

Un rapport d’eval doit lister :

- ce qui a été exécuté ;
- ce qui a changé ;
- score agrégé ;
- cas améliorés ;
- cas en régression ;
- cas flaky ou non concluants ;
- coût et latence ;
- résidus non résolus ;
- décision de promotion.

Stockez les rapports près du harness d’eval ou dans un emplacement d’artifact documenté, et liez les changements de direction importants depuis `evolution/`.
