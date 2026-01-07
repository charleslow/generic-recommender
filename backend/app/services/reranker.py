"""Reranking services using ZeroEntropy or LLM."""
from zeroentropy import ZeroEntropy

from app.config import settings
from app.services.llm import rerank_with_llm


async def rerank_with_zeroentropy(
    user_context: str,
    items: list[dict],
    model: str = "zerank-2",
) -> list[dict]:
    """
    Rerank items using ZeroEntropy's zerank models.
    
    Args:
        user_context: The user's context/query
        items: List of item dicts with 'item_id', 'title', 'text'
        model: ZeroEntropy model name (e.g., 'zerank-2')
    
    Returns:
        Reranked list of items with scores
    """
    # Initialize the client (ensure API key is set in environment or passed here)
    client = ZeroEntropy(api_key=settings.zeroentropy_api_key)
    
    # Prepare documents for reranking (List of strings)
    documents = [f"{item['title']}: {item['text']}" for item in items]
    
    # Call ZeroEntropy rerank API
    response = client.models.rerank(
        model=model,
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
    rerank_model: str,
) -> list[dict]:
    """
    Rerank items using specified model.
    
    Args:
        user_context: The user's context/query
        items: List of item dicts
        rerank_model: 'zerank-*' for ZeroEntropy, or an LLM model name
    
    Returns:
        Reranked list of items with scores
    """
    if rerank_model.startswith("zerank"):
        return await rerank_with_zeroentropy(user_context, items, rerank_model)
    else:
        return await rerank_with_llm(user_context, items, rerank_model)
