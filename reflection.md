# Reflection: Prompt Engineering Justifications

## Vue d'ensemble

Le **system prompt** est la fondation du comportement du chatbot. Il doit simultanément : 
1. Imposer une discipline stricte (répondre UNIQUEMENT du contexte)
2. Assurer la qualité (citer les sources exactes)
3. Gérer les cas limites (questions hors scope)
4. Maintenir la professionnalité (français, tonalité e-commerce)

---

## 1. **Identité et Tonalité Professionnelle**

### Choix : "Assistant spécialisé en support client e-commerce"

**Justification:**
- Oriente le modèle vers un domaine spécifique (vs. assistant générique)
- Force la tonalité "professionnel, concis, courtois" → réduit les digressions
- Français dès le système prompt → cohérence linguistique garantie
- E-commerce plutôt que "support général" → améliore la pertinence métier

**Test:** Sans cette spécialisation, Granite répondrait en style académique ou avec expressions inutiles.

---

## 2. **Contrainte Stricte : "Répondre UNIQUEMENT à partir du contexte"**

### Choix : Instructions explicites + refus poli structuré

**Justification:**
- **Hallucinations minimisées** : dire "non" aux questions hors scope évite les faux positifs
- **Confiance utilisateur amplifiée** : l'utilisateur sait qu'une réponse = sourcée
- **Chaîne de responsabilité claire** : pas d'ambiguïté sur la source de la réponse
- Instructions en 3 niveaux (Si/Sinon/Sinon) → force le modèle à classifier d'abord

**Technique utilisée: GuardRails explicites**
```
1. Si réponse COMPLÈTE trouvée → fournis + source
2. Si réponse PARTIELLE → dis quoi est/n'est pas couvert
3. Si PAS trouvé → refuse poliment + suggère une action
```

---

## 3. **Chain-of-Thought Reasoning**

### Choix : Étapes intermédiaires visibles

**Justification:**
- **Meilleure fidélité aux sources** : le modèle "réfléchit" en citant avant de répondre
- **Debugging facilité** : on voit la chaîne logique du modèle
- **Reduction des erreurs associatives** : Granite doit expliciter son raisonnement
- Exemple d'amélioration :
  ```
  # SANS Chain-of-Thought
  Question: "Politique de retour ?"
  Réponse: "30 jours" ❌ (pas d'explication pourquoi c'est 30)
  
  # AVEC Chain-of-Thought
  "Je cherche dans les documents... Les conditions générales disent:
   article 3 = politique retour pour électronique de 30 jours.
   Réponse: 30 jours pour électronique ✅ (trace visible)
  ```

---

## 4. **Format de Réponse Structuré : Couverture Explicite**

### Choix : 3 champs (Réponse + Sources + Couverture)

**Justification:**
- **Couverture: complete** → LLM donne réponse exhaustive du corpus
- **Couverture: partial** → certains aspects manquent, signalé à l'utilisateur
- **Couverture: not_available** → refuse poliment (pas visible à l'API, code 404)

Cela améliore la **confiance** : l'utilisateur sait exactement si la réponse est :
- Complète (faire confiance sans hésitation)
- Partielle (prendre avec recul, demander clarification)
- Absente (relancer vers support)

---

## 5. **Technique Avancée Choisie : Chain-of-Thought + GuardRails**

(Vs. alternatives: few-shot ex., prompt engineering classique, ou retrieval augmentation)

### Pourquoi pas Few-Shot Examples ?
- **Coût en tokens** : chaque exemple mange du contexte (500+ chars)
- **Illusion de généralisation** : 2-3 exemples ne couvrent pas la variété e-commerce
- **Maintenance** : ajouter des cas limites demande refonte constante

### Pourquoi Chain-of-Thought + GuardRails ?
- **Léger** : 200 tokens seulement vs. 1000+ pour few-shot
- **Scalable** : fonctionne pour toute catégorie de question
- **Transparent** : on voit le raisonnement
- **Robuste** : guérit les défauts de Granite (confabulation, citation imprécise)

---

## 6. **Limitations Identifiées**

### 🔴 Limitation 1 : Dépendance au contexte de qualité
**Problème:** Si les documents sont mal structurés, le LLM recrache du bruit.  
**Solution possible:** Pré-traiter les documents → extraction d'entités avant indexation.

### 🔴 Limitation 2 : Pas de mise à jour en temps réel
**Problème:** Ajouter 1000 documents = ré-indexation complète (10 min+).  
**Solution possible:** FAISS incrémental (add_documents), mais avec risque d'hallucinations croissantes.

### 🔴 Limitation 3 : Threshold arbitraire pour "hors scope"
**Problème:** Comment le LLM décide-t-il "couverture = not_available" ?  
**Raison:** Pas de scoring objectif, juste "absence de pattern dans réponse".  
**Solution possible:** Ajouter confidence score avec BERTScore ou similarité document-réponse.

---

## 7. **Ce que je Ferais Différemment avec Plus de Temps**

### À Court Terme (1-2 jours)
1. **Évaluation quantitative** : RAGAS benchmark sur 100 questions
2. **Threshold tuning** : trouver le meilleur rapport precision/recall
3. **Few-shot si impact > 5%** : ajouter 2-3 exemples si ça aide vraiment

### À Moyen Terme (1-2 semaines)
1. **Hybrid retrieval** : combiner lexical (BM25) + sémantique (FAISS)
2. **LLM caching** : Prompt Cache pour les contextes récurrents
3. **Multi-modèles** : tester Llama3.1, Mistral contre Granite

### À Long Terme (1+ mois)
1. **Agentic RAG** : donner des "outils" au LLM (recherche supplémentaire, calculs)
2. **Reranker neutre** : cross-encoder pour re-scorer les documents
3. **Fine-tuning** : adapter Granite sur corpus e-commerce spécifique

---

## 8. **Conclusion**

Le prompt choisi implémente une **approche pragmatique** :
- ✅ Robuste contre hallucinations (GuardRails)
- ✅ Transparent (Chain-of-Thought)
- ✅ Léger en tokens (scalable)
- ✅ Approprié pour MVP production

Le trade-off accepté : **pas de perfection**, juste une **fiabilité acceptable** pour support e-commerce.
