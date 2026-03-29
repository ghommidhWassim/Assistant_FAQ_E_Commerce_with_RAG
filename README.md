# RAG Chatbot — E-commerce Support Assistant

Un chatbot RAG (Retrieval-Augmented Generation) basé sur des documents pour fournir des réponses précises et sourcées aux questions e-commerce. Le système combine la récupération sémantique de documents avec la génération LLM pour garantir des réponses fidèles à la source.

## 📋 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT (HTTP REST)                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┴──────────────┐
        │   POST /ask                │
        │   GET /health              │
        └─────────────┬──────────────┘
                      │
    ┌─────────────────▼────────────────────┐
    │      Flask REST API (app.py)         │
    │  - Input validation & error handling │
    │  - Response formatting               │
    └─────────────────┬────────────────────┘
                      │
    ┌─────────────────▼─────────────────────────────────────┐
    │         LLM RAG Handler (llm_rag.py)                  │
    │  ┌────────────────────────────────────────────────┐   │
    │  │ 1. Document Retrieval (Semantic Search)       │   │
    │  │    - Query embedding via Ollama               │   │
    │  │    - FAISS similarity search (k=5)            │   │
    │  ├────────────────────────────────────────────────┤   │
    │  │ 2. Prompt Engineering (Chain-of-Thought)      │   │
    │  │    - System prompt with French instructions   │   │
    │  │    - Context formatting with sources          │   │
    │  │    - Guardrails for out-of-scope questions    │   │
    │  ├────────────────────────────────────────────────┤   │
    │  │ 3. LLM Inference (Granite via Ollama)         │   │
    │  │    - Generate contextualized response         │   │
    │  │    - Chain-of-thought reasoning               │   │
    │  ├────────────────────────────────────────────────┤   │
    │  │ 4. Post-Processing                            │   │
    │  │    - Source extraction & citation             │   │
    │  │    - Coverage assessment                      │   │
    │  │    - Confidence scoring                       │   │
    │  └────────────────────────────────────────────────┘   │
    └─────────────────┬─────────────────────────────────────┘
                      │
    ┌─────────────────▼─────────────────────────────────────┐
    │        Vector Store & Data Layer                      │
    │  ┌────────────────────────────────────────────────┐   │
    │  │ FAISS Vector Store (vector_store.py)          │   │
    │  │  - Persistent index (faiss_index/)            │   │
    │  │  - Embedding generation (Ollama)              │   │
    │  │  - Chunk similarity search                    │   │
    │  └────────────────────────────────────────────────┘   │
    │  ┌────────────────────────────────────────────────┐   │
    │  │ Document Processing                           │   │
    │  │  - PDF parsing (PyPDF)                        │   │
    │  │  - Text chunking (RecursiveCharacterSplitter) │   │
    │  │  - Metadata tracking                          │   │
    │  └────────────────────────────────────────────────┘   │
    └─────────────────┬─────────────────────────────────────┘
                      │
        ┌─────────────┴──────────────────────┐
        │  Data Sources (data/)              │
        │  - FAQ.json                        │
        │  - Ecommerce_FAQ_dataset.json      │
        └────────────────────────────────────┘
```

## 🎯 Composants Principaux

### 1. **Document Ingestion** (`vector_store.py`)
- Chargement de fichiers PDF, JSON, texte
- Découpage cohérent en chunks (500 tokens, chevauchement 50)
- Extraction des métadonnées (source, page)

### 2. **Vectorisation** (`vector_store.py`)
- Génération d'embeddings via **Ollama (Granite)**
- Indexation persistante en **FAISS**
- Recherche rapide par similarité sémantique

### 3. **Retrieval Contextuel** (`vector_store.py`)
- Requête utilisateur → embedding
- Récupération des k=5 chunks les plus pertinents
- Formatage avec métadonnées de source

### 4. **Génération Augmentée** (`llm_rag.py`)
- **System Prompt** en français avec instructions strictes
- **Chain-of-Thought** reasoning explicite
- **Source Citation** obligatoire
- **Guardrails** pour les questions hors scope

### 5. **API & Exposition** (`app.py`)
- **POST /ask** : soumettre une question
- **GET /health** : vérifier le statut
- Gestion complète des erreurs
- Validation des requêtes

## 🚀 Setup Rapide (< 3 minutes)

### Prérequis
- Python 3.9+
- Ollama installé et recevant les modèles (`ollama pull granite3.3`)
- Ollama lancé (`ollama serve`)

### Installation

**1. Cloner et configuration**
```bash
cd rag_chatbot
cp .env.example .env
pip install -r requirements.txt
```

**2. Lancer l'API**
```bash
cd src
python app.py
```

L'API sera disponible sur `http://localhost:5000`

### Via Docker

```bash
# Build l'image
docker build -f src/dockerfile -t rag-chatbot .

# Lancer le conteneur
docker run -p 5000:5000 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/faiss_index:/app/faiss_index \
  rag-chatbot
```

## 📡 Utilisation de l'API

### 1. Vérifier le statut
```bash
curl -X GET http://localhost:5000/health
```

**Réponse:**
```json
{
  "status": "ok",
  "message": "RAG API is running",
  "model": "granite3.3"
}
```

### 2. Poser une question
```bash
curl -X POST http://localhost:5000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Quelle est la politique de retour ?"}'
```

**Réponse:**
```json
{
  "answer": "La politique de retour est de 30 jours pour tout produit non endommagé avec le reçu original...",
  "sources": ["FAQ.json", "Ecommerce_FAQ_dataset.json"],
  "confidence": "high",
  "coverage": "complete"
}
```

### 3. Question hors contexte
```bash
curl -X POST http://localhost:5000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Quel est le meilleur restaurant à Paris ?"}'
```

**Réponse (404):**
```json
{
  "error": "Cette question n'est pas couverte par les documents disponibles...",
  "coverage": "not_available"
}
```

## 🔧 Choix Techniques Justifiés

| Composant | Choix | Justification |
|-----------|-------|---------------|
| **LLM** | Granite 3.3 via Ollama | Exécution locale, aucune donnée externe, latence faible, gratuit |
| **Vector Store** | FAISS | Haut performance, léger, persistant, parfait pour <1M documents |
| **Embeddings** | Ollama (Granite) | Cohérence avec le même modèle, pas de dépendance externe |
| **Framework Web** | Flask | Léger, simple, idéal pour MVP et APIs REST |
| **Chunking** | RecursiveCharacterSplitter | Préserve couches de sens, évite fragmentations aléatoires |
| **Langage** | Français dans système prompt | Qualité de réponse + tonalité professionnelle |

## 📊 Exemple de Flux Complet

1. **Entrée utilisateur:**
   ```
   "Ai-je droit à une garantie sur les articles électroniques ?"
   ```

2. **Étape 1 — Retrieval:**
   - Embedding de la question
   - Recherche FAISS des 5 chunks proches
   - Récupération: ["FAQ.json: garantie", "conditions_generales.txt: électronique"]

3. **Étape 2 — Prompt Construction:**
   ```
   Système: [Instructions strictes + français + sources]
   Contexte: [5 chunks avec métadonnées]
   Question: [question utilisateur]
   ```

4. **Étape 3 — LLM Inference:**
   - Granite génère réponse + sources en français
   - Chain-of-thought explicite

5. **Étape 4 — Post-Processing:**
   - Extraction sources → ["FAQ.json", "conditions_generales.txt"]
   - Couverture → "complete" (réponse exhaustive trouvée)
   - Confiance → "high" (5 docs pertinents)

6. **Réponse API:**
   ```json
   {
     "answer": "Oui, les articles électroniques bénéficient d'une garantie de 2 ans...",
     "sources": ["FAQ.json", "conditions_generales.txt"],
     "confidence": "high",
     "coverage": "complete"
   }
   ```

## 📂 Structure Projet

```
rag_chatbot/
├── src/
│   ├── app.py                          # API Flask (endpoints /ask, /health)
│   ├── llm_rag.py                      # Orchestration RAG + Prompting
│   ├── vector_store.py                 # Gestion FAISS + Documents
│   ├── conversation.py                 # Persistance historique (bonus)
│   └── dockerfile                      # Docker packaging
├── data/                               # Documents corpus
│   ├── FAQ.json
│   └── Ecommerce_FAQ_dataset.json
├── data_sources.md                     # Métadonnées sources (requis)
├── reflection.md                       # Justifications prompting (requis)
├── eval/                               # Tests d'évaluation (bonus)
│   └── evaluation.py
├── requirements.txt                    # Dépendances Python
├── .env.example                        # Template configuration
├── README.md                           # Ce fichier
└── LICENSE                             # MIT
```

## ⚙️ Configuration Avancée

### Variables Environnement (.env)
```env
# API
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False

# LLM
LLM_MODEL=granite3.3
OLLAMA_BASE_URL=http://localhost:11434

# Data
DATA_DIR=data
VECTOR_STORE_PATH=faiss_index
CHUNK_SIZE=500          # tokens par chunk
CHUNK_OVERLAP=50        # chevauchement
```

## 🧪 Tests

### Requête valide - Question couverte
```bash
curl -X POST http://localhost:5000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Quel est le délai de livraison standard ?"}'
```

### Requête invalide - Question vide
```bash
curl -X POST http://localhost:5000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": ""}'
```
→ Erreur 400: "Question cannot be empty"

### Requête hors contexte
```bash
curl -X POST http://localhost:5000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Comment faire un gâteau au chocolat ?"}'
```
→ Erreur 404: "Cette question n'est pas couverte..."

## 📄 License
MIT License. See LICENSE for details.
