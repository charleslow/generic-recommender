"""LLM services using OpenRouter and Groq APIs."""
import json
import re

from app.config import EMBEDDING_MODELS, settings
from groq import AsyncGroq
from openai import AsyncOpenAI

TEXT_LIMIT = 200

# OpenRouter client (OpenAI-compatible)
openrouter_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.openrouter_api_key,
)

# Groq client
groq_client = AsyncGroq(
    api_key=settings.groq_api_key,
)


def _parse_model(model: str) -> tuple[str, str]:
    """
    Parse a model string to extract provider and model name.
    
    Args:
        model: Model string like "openrouter/openai/gpt-4o-mini" or "groq/llama-3.3-70b-versatile"
    
    Returns:
        Tuple of (provider, model_name)
    """
    if model.startswith("openrouter/"):
        return "openrouter", model[len("openrouter/"):]
    elif model.startswith("groq/"):
        return "groq", model[len("groq/"):]
    else:
        # Default to openrouter for backward compatibility
        return "openrouter", model

# Lazy-loaded SentenceTransformer models (cached for performance)
_sentence_transformer_models: dict = {}


def _parse_json_array(content: str | None) -> list:
    """
    Robustly parse a JSON array from LLM response.
    
    Handles:
    - Markdown code blocks (```json ... ``` or ``` ... ```)
    - Leading/trailing whitespace and text
    - Arrays embedded in explanatory text
    - Python-style single quotes instead of double quotes
    - Trailing commas
    """
    if not content:
        raise ValueError("LLM returned empty response")
    
    content = content.strip()
    
    # Remove markdown code blocks if present
    if "```" in content:
        # Extract content between code blocks
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL)
        if match:
            content = match.group(1).strip()
    
    # Try to find a JSON array in the content
    # Look for content between [ and ]
    match = re.search(r"\[.*\]", content, re.DOTALL)
    if match:
        content = match.group(0)
    
    # First attempt: try parsing as-is
    try:
        result = json.loads(content)
        if isinstance(result, list):
            return result
        raise ValueError(f"Expected JSON array, got {type(result).__name__}")
    except json.JSONDecodeError:
        pass  # Try fixes below
    
    # Fix common LLM issues:
    # 1. Replace single quotes with double quotes (Python-style lists)
    # 2. Remove trailing commas before ] or }
    fixed_content = content
    
    # Replace single quotes with double quotes for string values
    # This regex handles: 'value' -> "value"
    fixed_content = re.sub(r"'([^']*)'", r'"\1"', fixed_content)
    
    # Remove trailing commas (e.g., ["a", "b",] -> ["a", "b"])
    fixed_content = re.sub(r",\s*([}\]])", r"\1", fixed_content)
    
    try:
        result = json.loads(fixed_content)
        if isinstance(result, list):
            return result
        raise ValueError(f"Expected JSON array, got {type(result).__name__}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON array: {e}. Content: {content[:200]}")


async def generate_synthetic_candidates(
    user_context: str,
    model: str,
    system_prompt: str | None = None,
) -> list[str]:
    """
    Generate synthetic item candidates using an LLM.
    
    Args:
        user_context: The user's context/query
        model: OpenRouter model name (e.g., 'openai/gpt-4o-mini')
        system_prompt: Custom system prompt (uses default from settings if not provided)
    
    Returns:
        List of synthetic candidate strings
    """
    # Use provided system prompt or fall back to default
    effective_prompt = system_prompt if system_prompt else settings.system_prompt
    
    prompt = f"""{effective_prompt}

Generate {settings.num_synthetic} recommendations for the following user context. 
Return ONLY a JSON array of strings, each being a short title/name.

User Context:
{user_context}

Response format: ["candidate1", "candidate2", ...]"""

    provider, model_name = _parse_model(model)
    
    if provider == "groq":
        response = await groq_client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            reasoning_effort="none",  # Disable thinking/reasoning
        )
    else:  # openrouter
        response = await openrouter_client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            extra_body={"reasoning": {"effort": "none"}},  # Disable thinking/reasoning
        )
    
    content = response.choices[0].message.content
    candidates = _parse_json_array(content)
    return candidates[:settings.num_synthetic]


def _get_sentence_transformer(model_name: str):
    """Get or load a SentenceTransformer model (cached for performance)."""
    global _sentence_transformer_models
    
    if model_name not in _sentence_transformer_models:
        from sentence_transformers import SentenceTransformer
        print(f"Loading SentenceTransformer model: {model_name}")
        _sentence_transformer_models[model_name] = SentenceTransformer(model_name)
    
    return _sentence_transformer_models[model_name]


async def embed_texts(texts: list[str], embedding_model: str = "openai") -> list[list[float]]:
    """
    Embed texts using the specified embedding model.
    
    Args:
        texts: List of texts to embed
        embedding_model: Key of the embedding model to use ('openai', 'qwen', 'gist')
    
    Returns:
        List of embedding vectors
    """
    if embedding_model not in EMBEDDING_MODELS:
        raise ValueError(f"Unknown embedding model: {embedding_model}. Available: {list(EMBEDDING_MODELS.keys())}")
    
    model_config = EMBEDDING_MODELS[embedding_model]
    model_name = model_config["name"]
    model_type = model_config["type"]
    
    if model_type == "sentence_transformer":
        # Use local SentenceTransformer
        import asyncio
        
        def _encode():
            model = _get_sentence_transformer(model_name)
            embeddings = model.encode(texts, convert_to_numpy=True)
            return embeddings.tolist()
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(None, _encode)
        return embeddings
    
    elif model_type == "openrouter":
        # Use OpenRouter API
        response = await openrouter_client.embeddings.create(
            model=model_name,
            input=texts,
        )
        
        # Sort by index to ensure correct order
        embeddings_data = sorted(response.data, key=lambda x: x.index)
        return [item.embedding for item in embeddings_data]
    
    else:
        raise ValueError(f"Unknown model type: {model_type}")


async def rerank_with_llm(
    user_context: str,
    items: list[dict],
    model: str,
    system_prompt: str | None = None,
) -> list[dict]:
    """
    Rerank items using an LLM.
    
    Args:
        user_context: The user's context/query
        items: List of item dicts with 'item_id', 'title', 'text'
        model: OpenRouter model name
        system_prompt: Custom system prompt (uses default from settings if not provided)
    
    Returns:
        Reranked list of items with scores
    """
    # Use provided system prompt or fall back to default
    effective_prompt = system_prompt if system_prompt else settings.system_prompt
    
    # Build numbered list of items with their IDs clearly marked
    items_text = "\n".join([
        f"- ID: {item['item_id']} | Title: {item['title']} | Description: {item['text'][:TEXT_LIMIT]}"
        for item in items
    ])
    
    # Get list of valid IDs for the prompt
    valid_ids = [item['item_id'] for item in items]
    
    prompt = f"""{effective_prompt}

Your task is to rank items by relevance to the user.

USER CONTEXT:
{user_context}

AVAILABLE ITEMS:
{items_text}

TASK:
Select the {settings.num_results} most relevant items for this user and return their IDs.

RESPONSE FORMAT:
You must respond with ONLY a JSON array of item IDs, nothing else.
The array should contain exactly {settings.num_results} item IDs in order of relevance (most relevant first).
Use the exact item IDs from the list above.

Valid IDs are: {valid_ids}

YOUR RESPONSE (JSON array only):"""

    provider, model_name = _parse_model(model)
    
    if provider == "groq":
        response = await groq_client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            reasoning_effort="none",  # Disable thinking/reasoning
        )
    else:  # openrouter
        response = await openrouter_client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            extra_body={"reasoning": {"effort": "none"}},  # Disable thinking/reasoning
        )
    
    content = response.choices[0].message.content
    ranked_ids = _parse_json_array(content)
    
    # Build result with scores (descending from 1.0)
    id_to_item = {item["item_id"]: item for item in items}
    ranked_items = []
    for i, item_id in enumerate(ranked_ids[:settings.num_results]):
        if item_id in id_to_item:
            item = id_to_item[item_id].copy()
            item["score"] = 1.0 - (i * 0.1)  # Simple descending score
            ranked_items.append(item)
    
    return ranked_items
    return ranked_items
