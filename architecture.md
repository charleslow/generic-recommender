# Generic Recommender - POC Architecture

## Final Stack

| Layer | Choice |
|-------|--------|
| **Frontend** | React on Firebase Hosting |
| **Backend** | FastAPI on Cloud Run (min 1 instance) |
| **Vector Search** | FAISS in-memory |
| **Embeddings Storage** | Bundled in Docker image (numpy binary) |
| **Metadata/Config** | Bundled in Docker image (JSON) |
| **LLM** | OpenRouter API |
| **Reranker** | ZeroEntropy (zerank-2) OR OpenRouter LLM (selectable) |

---

## Project Structure

```
generic-recommender/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry
│   │   ├── config.py            # Hardcoded config (loaded from yaml)
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   └── recommend.py     # /recommend endpoint
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── llm.py           # OpenRouter LLM calls
│   │   │   ├── vector_search.py # FAISS operations
│   │   │   └── reranker.py      # ZeroEntropy + LLM reranking
│   │   └── models/
│   │       ├── __init__.py
│   │       └── schemas.py       # Pydantic models
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── QueryInput.tsx
│   │   │   ├── ResultsList.tsx
│   │   │   ├── ModelSelector.tsx
│   │   │   └── LatencyDisplay.tsx
│   │   └── api/
│   │       └── recommend.ts
│   ├── package.json
│   ├── firebase.json
│   └── .firebaserc
├── scripts/
│   └── embed_catalogue.py       # Offline: embed items → numpy
├── user_inputs/                 # Gitignored
│   ├── catalogue.jsonl          # User's item catalogue
│   └── config.yaml              # User's config
├── .gitignore
├── concept.md
└── architecture.md
```

---

## API Design

### `POST /recommend`

**Request:**
```json
{
  "user_context": "I want a job in AI and gaming...",
  "llm_model": "openai/gpt-4o-mini",
  "rerank_model": "zerank-2"  // or an LLM model name like "openai/gpt-4o-mini"
}
```

**Response:**
```json
{
  "recommendations": [
    {"item_id": "123", "title": "AI Engineer", "score": 0.95},
    {"item_id": "456", "title": "Game Developer", "score": 0.89}
  ],
  "latency_ms": {
    "candidate_generation": 320,
    "vector_search": 15,
    "reranking": 280,
    "total": 615
  },
  "debug": {
    "synthetic_candidates": ["AI Engineer", "ML Researcher", ...],
    "num_retrieved": 50
  }
}
```

### `GET /health`
Health check for Cloud Run.

### `GET /models`
Returns available LLM models for frontend dropdown.

---

## Config Schema (`user_inputs/config.yaml`)

```yaml
system_prompt: "You are a career guidance assistant to suggest future pathways for youth."
item_type: "job"
num_candidates: 50       # Retrieved from vector search
num_results: 5           # Final recommendations
num_synthetic: 10        # Synthetic candidates from LLM

available_models:
  - openai/gpt-4o-mini
  - anthropic/claude-3-haiku
  - meta-llama/llama-3.1-70b-instruct
```

---

## Environment Variables

```bash
# Backend (.env)
OPENROUTER_API_KEY=sk-or-...
ZEROENTROPY_API_KEY=ze-...
```

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         PRECOMPUTATION                          │
├─────────────────────────────────────────────────────────────────┤
│  catalogue.jsonl → embed_catalogue.py → embeddings.npy          │
│                           ↓                    catalogue.json   │
│              Copy to backend/data/ → Bundle in Docker image     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      INFERENCE (Cloud Run)                      │
├─────────────────────────────────────────────────────────────────┤
│  1. Startup: Load embeddings from /app/data → FAISS index       │
│  2. Startup: Load catalogue metadata from /app/data             │
│                                                                 │
│  3. Request: user_context arrives                               │
│        ↓                                                        │
│  4. LLM (OpenRouter): Generate synthetic candidates             │
│        ↓                                                        │
│  5. Embed synthetic candidates (OpenRouter embedding)           │
│        ↓                                                        │
│  6. FAISS: kNN search for each candidate, merge scores          │
│        ↓                                                        │
│  7. Rerank: ZeroEntropy OR LLM reranking                        │
│        ↓                                                        │
│  8. Return top-k recommendations + latency breakdown            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Deployment Steps

### 1. Prepare Data
```bash
# Generate embeddings
python scripts/embed_catalogue.py

# Copy to backend for bundling
mkdir -p backend/data
cp user_inputs/embeddings.npy backend/data/
cp user_inputs/catalogue.json backend/data/
```

### 2. Firebase Setup
```bash
firebase login
firebase init hosting   # frontend only
```

### 3. Cloud Run Deployment
```bash
cd backend
gcloud run deploy generic-recommender \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --min-instances 1 \
  --memory 2Gi \
  --set-env-vars "OPENROUTER_API_KEY=sk-or-xxx,ZEROENTROPY_API_KEY=ze-xxx"
```

**Note**: Data is bundled in the Docker image. Redeploy when catalogue changes.

### 4. Frontend Deployment
```bash
cd frontend
npm run build
firebase deploy --only hosting
```

---

## Questions Before Implementation

1. **GCP Project**: Do you have an existing GCP project, or should I include setup instructions?

2. **Embedding at inference**: The synthetic candidates need to be embedded for vector search. Should I:
   - **Option A**: Call OpenRouter's embedding endpoint at inference (adds ~100-200ms latency)
   - **Option B**: Use a local lightweight embedding model in Cloud Run (faster, but larger container)

3. **CORS**: Frontend on Firebase Hosting → Backend on Cloud Run. I'll configure CORS. Any specific domain, or use `*` for POC?

4. **Ready to start coding?** If yes, I'll begin with the backend structure.
