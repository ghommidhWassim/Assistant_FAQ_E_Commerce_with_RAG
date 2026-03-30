## Justification du prompt engineering

Le prompt a été conçu pour contraindre fortement le modèle afin d’éviter les hallucinations, un problème fréquent dans les systèmes RAG. J’ai imposé des règles strictes : répondre uniquement à partir du contexte, citer les sources, et refuser les questions hors périmètre. L’ajout d’un format de sortie structuré (Réponse, Sources, Couverture) facilite le parsing automatique côté backend. J’ai également intégré une forme de chain-of-thought léger pour améliorer la précision sans exposer de raisonnement détaillé.

## Ce que je ferais différemment avec plus de temps

Avec plus de temps, j’améliorerais la qualité du retrieval en utilisant un reranker afin de mieux filtrer les documents pertinents. J’optimiserais également le module d’évaluation, car pour le moment l’exécution échoue, et j’intégrerais d’autres métriques pour une analyse plus complète. Enfin, j’ajouterais une interface de chat dynamique permettant de discuter avec l’agent, d’importer des documents et d’échanger directement à leur sujet.

## Limitation identifiée du système actuel
le système repose uniquement sur une similarité vectorielle simple, ce qui peut récupérer du contexte peu pertinent.
