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

```bash
# Set up Python environment with uv
cd generic-recommender
uv venv
source .venv/bin/activate
uv pip install openai numpy

# Set your OpenRouter API key
export OPENROUTER_API_KEY=sk-or-v1-xxxx

# Run embedding script
python scripts/embed_catalogue.py
```

This creates:
- `user_inputs/embeddings.npy` - numpy array of embeddings
- `user_inputs/catalogue.json` - catalogue metadata

### Copy data to backend

The embeddings are bundled directly into the Docker image for simplicity:

```bash
# Copy the generated files to the backend data directory
mkdir -p backend/data
cp user_inputs/embeddings.npy backend/data/
cp user_inputs/catalogue.json backend/data/
```

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

### Test locally first

```bash
cd backend
uv pip install -r requirements.txt

uvicorn app.main:app --reload --port 8080

# Test the API
curl http://localhost:8080/health
curl http://localhost:8080/models
```

### Deploy to Cloud Run

```bash
cd backend

# Deploy with environment variables
gcloud run deploy generic-recommender \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --min-instances 1 \
  --max-instances 3 \
  --memory 2Gi \
  --set-env-vars "OPENROUTER_API_KEY=sk-or-v1-xxxx,ZEROENTROPY_API_KEY=ze-xxxx"
```

**Important**: Using `--min-instances 1` keeps one instance warm to avoid cold starts.

**Note**: The embedding data is bundled into the Docker image. When you update your catalogue, re-run the embedding script and redeploy.

Note the deployed URL (e.g., `https://generic-recommender-xxxxx-uc.a.run.app`)

### Using Secret Manager (recommended for production)

```bash
# Create secrets
echo -n "sk-or-v1-xxxx" | gcloud secrets create openrouter-api-key --data-file=-
echo -n "ze-xxxx" | gcloud secrets create zeroentropy-api-key --data-file=-

# Grant Cloud Run access
gcloud secrets add-iam-policy-binding openrouter-api-key \
  --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding zeroentropy-api-key \
  --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Deploy with secrets
gcloud run deploy generic-recommender \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --min-instances 1 \
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

Create `.env.local` with your Cloud Run URL:

```bash
echo "VITE_API_URL=https://generic-recommender-xxxxx-uc.a.run.app" > .env.local
```

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
3. Select reranking method (`zerank-2` or `llm`)
4. Enter a user context:
   ```
   Career Direction: I want a job that aligns with my interests
   Areas of Interest: Tech, AI and Gaming
   Education: Bachelor of Computer Science
   ```
5. Click "Get Recommendations"
6. View:
   - **Recommendations** with scores
   - **Latency breakdown** for each component
   - **Debug info** showing synthetic candidates

---

## Troubleshooting

### Cloud Run cold starts
If you see slow first requests, ensure `--min-instances 1` is set.

### CORS errors
The backend is configured for `*` origins. If you need stricter CORS, edit `backend/app/main.py`.

### Embedding dimension mismatch
Ensure the same embedding model is used for precomputation and inference. Default is `openai/text-embedding-3-small` (1536 dimensions).

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
