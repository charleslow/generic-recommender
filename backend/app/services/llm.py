"""LLM services using OpenRouter API via OpenAI SDK."""
import json

from openai import AsyncOpenAI

from app.config import settings

# OpenRouter is OpenAI-compatible, so we use the OpenAI SDK with a custom base URL
client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.openrouter_api_key,
)


def _parse_json_response(content: str) -> list:
    """Parse JSON from LLM response, handling markdown code blocks."""
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]  # Remove first line
        content = content.rsplit("```", 1)[0]  # Remove last ```
    return json.loads(content)


async def generate_synthetic_candidates(
    user_context: str,
    model: str,
) -> list[str]:
    """
    Generate synthetic item candidates using an LLM.
    
    Args:
        user_context: The user's context/query
        model: OpenRouter model name (e.g., 'openai/gpt-4o-mini')
    
    Returns:
        List of synthetic candidate strings
    """
    prompt = f"""{settings.system_prompt}

Generate {settings.num_synthetic} {settings.item_type} recommendations for the following user context. 
Return ONLY a JSON array of strings, each being a short {settings.item_type} title/name.

User Context:
{user_context}

Response format: ["candidate1", "candidate2", ...]"""

    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    
    content = response.choices[0].message.content
    candidates = _parse_json_response(content)
    return candidates[:settings.num_synthetic]


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed texts using OpenRouter's embedding API.
    
    Args:
        texts: List of texts to embed
    
    Returns:
        List of embedding vectors
    """
    response = await client.embeddings.create(
        model=settings.embedding_model,
        input=texts,
    )
    
    # Sort by index to ensure correct order
    embeddings_data = sorted(response.data, key=lambda x: x.index)
    return [item.embedding for item in embeddings_data]


async def rerank_with_llm(
    user_context: str,
    items: list[dict],
    model: str,
) -> list[dict]:
    """
    Rerank items using an LLM.
    
    Args:
        user_context: The user's context/query
        items: List of item dicts with 'item_id', 'title', 'text'
        model: OpenRouter model name
    
    Returns:
        Reranked list of items with scores
    """
    items_text = "\n".join([
        f"{i+1}. [{item['item_id']}] {item['title']}: {item['text'][:200]}"
        for i, item in enumerate(items)
    ])
    
    prompt = f"""{settings.system_prompt}

# User Context
{user_context}

# Available Items
{items_text}

Select the top {settings.num_results} most relevant items for this user.
Return ONLY a JSON array of the item IDs in order of relevance (most relevant first).

Response format: ["item_id_1", "item_id_2", ...]"""

    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
    )
    
    content = response.choices[0].message.content
    ranked_ids = _parse_json_response(content)
    
    # Build result with scores (descending from 1.0)
    id_to_item = {item["item_id"]: item for item in items}
    ranked_items = []
    for i, item_id in enumerate(ranked_ids[:settings.num_results]):
        if item_id in id_to_item:
            item = id_to_item[item_id].copy()
            item["score"] = 1.0 - (i * 0.1)  # Simple descending score
            ranked_items.append(item)
    
    return ranked_items
