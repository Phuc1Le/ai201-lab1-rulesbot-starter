# Spec: `retrieve()`

**File:** `retriever.py`
**Status:** Spec incomplete — fill in all blank fields before implementing

---

## Purpose

Given a user's natural language query, find the most relevant chunks from the vector store using semantic similarity search. Return them ranked by relevance so that `generate_response()` can use them as context.

---

## Input / Output Contract

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | `str` | The user's natural language question |
| `n_results` | `int` | Maximum number of chunks to return (default: `N_RESULTS` from `config.py`) |

**Output:** `list[dict]`

Each dict in the returned list must contain exactly these keys:

| Key | Type | Description |
|-----|------|-------------|
| `"text"` | `str` | The chunk text |
| `"game"` | `str` | The game name this chunk came from |
| `"distance"` | `float` | Cosine distance score — lower means more similar to the query |

Results should be ordered from most to least relevant (lowest to highest distance). Returns an empty list `[]` if the collection contains no documents.

---

## Design Decisions

*Complete the fields below before writing any code. Use your AI tool in Plan or Ask mode to help you reason through what belongs here — but the decisions are yours.*

---

### Query approach

*Describe how you will use `_collection.query()` to find relevant chunks. What arguments will you pass, and why?*

```
I'll pass in raw query string, top_k 
```

---

### Return structure

*Sketch out what one item in your return list looks like as a concrete example. Where does each field come from in the query results?*

```
One item is a dict (not a list), matching the output contract:

{
    "text":     "On your turn, roll both dice. Every player collects resources
                 from tiles matching the rolled number...",
    "game":     "catan",
    "distance": 0.21,
}

Where each field comes from in the results of _collection.query(include=["documents", "metadatas", "distances"]):
  - "text"     <- results["documents"][0][i]
  - "game"     <- results["metadatas"][0][i]["game"]   (we stored {"game": ...} in embed_and_store)
  - "distance" <- results["distances"][0][i]

I build the list by zipping these three parallel lists together, one dict per chunk.
```

---

### Handling the nested result structure

*`_collection.query()` returns nested lists. Describe what index you need to access to get the actual list of results for a single query, and why the nesting exists.*

```
I need index [0].

query() accepts query_texts as a *list* because it supports batching many
queries in one call. So the return value is keyed by field, and each field
holds one inner list per query:

  results["documents"]  -> [ [doc, doc, doc] ]   # outer = queries, inner = chunks
  results["metadatas"]  -> [ [meta, meta, meta] ]
  results["distances"]  -> [ [dist, dist, dist] ]

I pass exactly one query, so the outer list has length 1. results["documents"][0]
unwraps that single query's results into the actual list of chunks (length up to
n_results). I then index [i] inside that to walk each chunk. Same [0] pattern for
metadatas and distances.
```

---

### Relevance threshold

*Will you filter out results above a certain distance score, or return all `n_results` regardless of how relevant they are? What are the tradeoffs of each approach?*

```
Decision: return all n_results (no hard threshold) for this lab, and let
generate_response() decide based on the chunks it gets.

Tradeoffs:
  - Threshold filtering: drops weakly-related chunks, so the LLM gets cleaner
    context and is less likely to hallucinate off an irrelevant rule. But with
    N_RESULTS = 3 (small), a too-strict cutoff can return 0 chunks even when a
    decent answer exists, and the "right" distance cutoff for cosine depends on
    the embedding model and is hard to tune by hand.
  - Return all n_results: simplest, always gives the LLM something to work with,
    and the distance scores are already returned so the prompt/LLM can judge
    relevance. Risk is feeding in a marginally-related chunk.

Since results are already ordered best-first and capped at n_results=3, the
extra cost of "too much context" is tiny. If hallucination from weak matches
becomes a problem, I can add a MAX_DISTANCE cutoff in config.py later.
```

---

### Edge cases

*How does your implementation behave when: (a) the collection is empty, (b) the query matches no chunks well, (c) the query matches chunks from multiple games?*

```
(a) Empty collection: the guard `if _collection.count() == 0: return []` runs
    first, so retrieve() returns [] without ever calling query(). This happens
    before any docs are ingested. generate_response() should treat an empty list
    as "no context available" rather than erroring.

(b) Poor matches: query() ALWAYS returns up to n_results chunks ranked by
    distance — there is no concept of "no match", just higher distance scores.
    Since I'm not thresholding (see Relevance threshold), I still return the
    top 3, but their large distances signal weak relevance. The distance values
    are in each returned dict, so generate_response()/the prompt can decide
    whether the context is good enough to answer or should say "I don't know."

(c) Multiple games: each result already carries its own "game" field from
    metadata, so a mixed-game result list is fine and expected — retrieve()
    does NOT try to disambiguate. retrieve() can't ask the user anything; if
    game disambiguation is needed, that belongs in the app loop or
    generate_response(), and could be supported here later via a metadata
    `where={"game": ...}` filter on query().
```

---

## Implementation Notes

*Fill this in after implementing, before moving to Milestone 3.*

**Test query and top result returned:**

```
Query: [your test query]
Top result game: [game name]
Distance score: [score]
Does it make sense? [yes / no / explain]
```

**One thing about the query results that surprised you:**

```
[your answer here]
```
