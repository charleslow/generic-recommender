# Generic Recommender - Setup Guide

This guide walks you through setting up the Generic Recommender POC from scratch.

## Prerequisites

- Google Cloud account with billing enabled
- Node.js 18+ and npm
- Python 3.11+
- API keys for:
  - [OpenRouter](https://openrouter.ai/) (for LLM and embeddings)
  - [ZeroEntropy](https://zeroentropy.ai/) (for zerank-2 reranking)

---

## 1. GCP Project Setup

### Create a new project

```bash
# Install gcloud CLI if not already installed
# https://cloud.google.com/sdk/docs/install

# Login to GCP
gcloud auth login

# Create a new project (or use existing)
gcloud projects create generic-recommender-poc --name="Generic Recommender POC"

# Set as default project
gcloud config set project generic-recommender-poc

# Enable billing (required for Cloud Run)
# Do this in the GCP Console: https://console.cloud.google.com/billing
```

### Enable required APIs

```bash
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com
```

---

## 2. Prepare Your Data

### Create your catalogue

Copy the sample and edit with your items:

```bash
cd generic-recommender
cp user_inputs/sample_catalogue.jsonl user_inputs/catalogue.jsonl
```

Each line must be valid JSON with these fields:
```json
{"item_id": "unique_id", "title": "Short Title", "text": "Detailed description for embedding..."}
```

### Embed the catalogue

The system supports multiple embedding models. You can generate embeddings for all models or select specific ones:

```bash
# Set up Python environment with uv
cd generic-recommender
uv venv
source .venv/bin/activate
uv pip install openai numpy sentence_transformers

# Set your OpenRouter API key
export OPENROUTER_API_KEY=sk-or-v1-xxxx

# Run embedding script for all models
python scripts/embed_catalogue.py --model all

# Or generate for specific models only:
# python scripts/embed_catalogue.py --model openai
# python scripts/embed_catalogue.py --model qwen
# python scripts/embed_catalogue.py --model gist
```

**Available embedding models:**
| Key | Model | Type | Dimensions |
|-----|-------|------|------------|
| `openai` | openai/text-embedding-3-small | OpenRouter API | 1536 |
| `qwen` | qwen/qwen3-embedding-8b | OpenRouter API | 4096 |
| `gist` | avsolatorio/GIST-all-MiniLM-L6-v2 | Local (SentenceTransformer) | 384 |

This creates:
- `user_inputs/embeddings_openai.npy` - OpenAI embeddings
- `user_inputs/embeddings_qwen.npy` - Qwen embeddings  
- `user_inputs/embeddings_gist.npy` - GIST embeddings (runs locally, no API needed)
- `user_inputs/catalogue.json` - catalogue metadata

### Copy data to backend

The embeddings are bundled directly into the Docker image for simplicity:

```bash
# Copy the generated files to the backend data directory
mkdir -p backend/data
cp user_inputs/embeddings_*.npy backend/data/
cp user_inputs/catalogue.json backend/data/
```

**Note:** Only copy the embedding files for models you want to support. Each embedding file adds to the Docker image size.

---

## 3. Deploy Backend to Cloud Run

### Configure environment

Create the backend `.env` file:

```bash
cd backend
cat > .env << EOF
OPENROUTER_API_KEY=sk-or-v1-xxxx
ZEROENTROPY_API_KEY=ze-xxxx
EOF
```

Export the environment variables to your shell:

```bash
export $(grep -v '^#' .env | xargs)
```

### Test locally first

The default `DATA_DIR` is set to `/app/data` for running in Docker. For local development, you need to override this to point to your local data folder:

```bash
cd backend
uv pip install -r requirements.txt

# Run with DATA_DIR pointing to local data folder
DATA_DIR=$(pwd)/data uvicorn app.main:app --reload --port 8080

# Test the API
curl http://localhost:8080/health
curl http://localhost:8080/models

# ZeroEntropy reranking
curl -X POST http://localhost:8080/recommend \
  -H "Content-Type: application/json" \
  -d '{"user_context": "I am interested in finance", "llm_model": "openai/gpt-4o-mini", "rerank_model": "zerank-2"}'

# LLM reranking
curl -X POST http://localhost:8080/recommend \
  -H "Content-Type: application/json" \
  -d '{"user_context": "I am interested in finance", "llm_model": "openai/gpt-4o-mini", "rerank_model": "anthropic/claude-3-haiku"}'
```

Alternatively, add `DATA_DIR` to your `.env` file:
```bash
echo "DATA_DIR=$(pwd)/data" >> .env
uvicorn app.main:app --reload --port 8080
```

### Deploy to Cloud Run

```bash
cd backend

# Export env vars if not already done
export $(grep -v '^#' .env | xargs)

# Create secrets from env vars
echo -n "$OPENROUTER_API_KEY" | gcloud secrets create openrouter-api-key --data-file=-
echo -n "$ZEROENTROPY_API_KEY" | gcloud secrets create zeroentropy-api-key --data-file=-

# Get project number and grant Cloud Run access to secrets
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)")

gcloud secrets add-iam-policy-binding openrouter-api-key \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding zeroentropy-api-key \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Deploy with secrets
gcloud run deploy generic-recommender \
  --source . \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --max-instances 2 \
  --set-secrets "OPENROUTER_API_KEY=openrouter-api-key:latest,ZEROENTROPY_API_KEY=zeroentropy-api-key:latest"
```

---

## 4. Deploy Frontend to Firebase Hosting

### Install Firebase CLI

```bash
npm install -g firebase-tools
firebase login
```

### Initialize Firebase project

```bash
cd frontend

# Initialize (select Hosting only)
firebase init hosting

# When prompted:
# - Select your GCP project
# - Public directory: dist
# - Single-page app: Yes
# - Don't overwrite index.html
```

### Configure API URL

Create `.env.local` in the frontend directory with your Cloud Run URL:

```bash
cd frontend
echo "VITE_API_URL=$(gcloud run services describe generic-recommender --region asia-southeast1 --format='value(status.url)')" > .env.local
```

### Test locally first

```bash
cd frontend
npm install
npm run dev
```

This starts the Vite dev server at `http://localhost:5173`. Test that:
- The app loads correctly
- Models are fetched from your Cloud Run backend
- Recommendations work with both reranking methods

### Build and deploy

```bash
cd frontend
npm install
npm run build
firebase deploy --only hosting
```

Your app is now live at `https://your-project-id.web.app`!

---

## 5. Testing the Full System

1. Open your Firebase Hosting URL
2. Select an LLM model (e.g., `openai/gpt-4o-mini`)
3. Select an embedding model (`openai`, `qwen`, or `gist`)
4. Select reranking method (`zerank-2` or an LLM model)
5. Enter a user context:
   ```
   Career Direction: I want a job that aligns with my interests
   Areas of Interest: Tech, AI and Gaming
   Education: Bachelor of Computer Science
   ```
6. Click "Get Recommendations"
7. View:
   - **Recommendations** with scores
   - **Latency breakdown** for each component
   - **Debug info** showing synthetic candidates and models used

---

## Troubleshooting

### Cloud Run cold starts
If you see slow first requests, ensure `--min-instances 1` is set.

### CORS errors
The backend is configured for `*` origins. If you need stricter CORS, edit `backend/app/main.py`.

### Embedding dimension mismatch
The system automatically uses the correct index for each embedding model. If you get dimension errors, ensure:
1. The embedding file (`embeddings_<model>.npy`) exists in `backend/data/`
2. You regenerated embeddings after any config changes: `python scripts/embed_catalogue.py --model all`

### ZeroEntropy API errors
Check your API key and ensure your account has access to `zerank-2`.

---

## Cost Estimates (POC)

| Service | Estimate |
|---------|----------|
| Cloud Run (1 min instance) | ~$15-30/month |
| Firebase Hosting | Free tier |
| OpenRouter (LLM calls) | Pay per token |
| ZeroEntropy (reranking) | Pay per request |

For a POC with light usage, expect **< $50/month** excluding API costs.

---

## Next Steps

- [ ] Add authentication (Firebase Auth)
- [ ] Support multiple catalogues
- [ ] Add config editing from frontend
- [ ] Implement caching for repeated queries
- [ ] Add request logging and analytics
