"""Reranking services using ZeroEntropy or LLM."""
from zeroentropy import ZeroEntropy

from app.config import settings
from app.services.llm import rerank_with_llm


async def rerank_with_zeroentropy(
    user_context: str,
    items: list[dict],
) -> list[dict]:
    """
    Rerank items using ZeroEntropy's zerank-2.
    
    Args:
        user_context: The user's context/query
        items: List of item dicts with 'item_id', 'title', 'text'
    
    Returns:
        Reranked list of items with scores
    """
    # Initialize the client (ensure API key is set in environment or passed here)
    client = ZeroEntropy(api_key=settings.zeroentropy_api_key)
    
    # Prepare documents for reranking (List of strings)
    documents = [f"{item['title']}: {item['text']}" for item in items]
    
    # Call ZeroEntropy rerank API
    # Update 1: Access via the 'models' namespace
    # Update 2: Use the 'zerank-2' model (latest SOTA model)
    response = client.models.rerank(
        model="zerank-2",
        query=user_context,
        documents=documents,
        top_n=settings.num_results,
    )
    
    # Map results back to items
    ranked_items = []
    for result in response.results:
        # The 'index' attribute maps back to the original list position
        item = items[result.index].copy()
        item["score"] = result.relevance_score
        ranked_items.append(item)
    
    return ranked_items


async def rerank_items(
    user_context: str,
    items: list[dict],
    method: str,
    llm_model: str = "openai/gpt-4o-mini",
) -> list[dict]:
    """
    Rerank items using specified method.
    
    Args:
        user_context: The user's context/query
        items: List of item dicts
        method: 'zerank-2' or 'llm'
        llm_model: LLM model to use if method is 'llm'
    
    Returns:
        Reranked list of items with scores
    """
    if method == "zerank-2":
        return await rerank_with_zeroentropy(user_context, items)
    elif method == "llm":
        return await rerank_with_llm(user_context, items, llm_model)
    else:
        raise ValueError(f"Unknown rerank method: {method}")
