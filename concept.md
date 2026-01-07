# Generic Recommender

This is a generic recommender service. The idea is to be able to control item recommendations using prompts.
The aim is end-to-end latency of `<1s`.

## User Inputs

Create a folder called `user_inputs/`, which is git-kept but empty. Can provide some dummy sample items to help user know what to put in.

**Item catalogue**. User supplies an item catalogue in a `.jsonl` file. Required fields:
- `item_id`: unique identifier for the item
- `title`: short descriptor for the item (for display purposes)
- `text`: text representation for the item (to be embedded)

**Configuration**. In a `.yaml` file, the user supplies a configuration for the system. This includes:
- `system_prompt`: the system prompt guiding behaviour of the system
    - e.g. `You are a career guidance assistant to suggest future pathways for youth`.
- `item_type`: the type of item we are recommending, e.g. `job`
- `num_candidates`: the number of synthetic candidates to retrieve and send for reranking
- `num_results`: the final number of recommendations to return

## Precomputation

- The items in the supplied catalogue are embedded using some embedding model from openrouter.
- They are indexed and stored in a simple vector DB for nearest neighbour search later

## Inference Time

At inference time, user supplies a `user_context` to get recommendations. For e.g.

```
Career Direction: I want a job that aligns with my interests and hobbies
Areas of Interest: Tech, AI and Gaming
Diploma: DIPLOMA IN INFO TECH
Degree: BACHELOR OF COMP. SCIENCE
```

First, we use an LLM to generate synthetic item candidates for the user. This is using an LLM openrouter call.
The meta prompt is:

```
{system_prompt} Generate some {item_type} recommendations for {user_context}. Provide a list of strings.
```

Second, we use the candidates to look up the pre-computed vector database to retrieve nearest neighbours.
- Since we have multiple item candidates, we will do multiple kNN retrievals.
- The scores can be summed for each candidate and ranked in descending score order.
- `num_candidates` items will be sent for reranking

Third, we do reranking using an LLM OR a cross encoder reranker (like `zerank`).
- This will return the top recommendations to the user
- The meta prompt is `{system_prompt} # User context\n\n{user_context}\n\n # Items\n\n{item_candidates}. Choose the top {num_results} items for the user.`
- The top items are then returned to the user

## Frontend

We want a simple frontend for users to test out different `user_context` queries and experience the latency.
- User clicks pre-stored catalogue from a drop-down
- User types `user_context` into a query box and gets recommendations
- (Optional) user gets to select LLM model used for candidate generation or reranking