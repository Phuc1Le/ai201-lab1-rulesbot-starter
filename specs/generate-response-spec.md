# Spec: `generate_response()`

**File:** `generator.py`
**Status:** Spec incomplete — fill in all blank fields before implementing

---

## Purpose

Given a user query and a list of retrieved rule chunks, generate a response that directly answers the question using only the retrieved text as context. The response must be grounded — it should not draw on the model's general knowledge of board games, only on what was retrieved.

---

## Input / Output Contract

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | `str` | The user's original question |
| `retrieved_chunks` | `list[dict]` | Ranked list of chunks from `retrieve()`, each with `"text"`, `"game"`, and `"distance"` |

**Output:** `str`

A plain string containing the response to show the user. The response should:
- Answer the question using only the retrieved rule text
- Identify which game the answer comes from
- Acknowledge clearly when the answer is not found in the loaded rules

Returns a fallback string (not an error) when `retrieved_chunks` is empty.

---

## Design Decisions

*Complete the fields below before writing any code. Use your AI tool in Plan or Ask mode to help you reason through what belongs here — but the decisions are yours.*

---

### Context formatting

*How will you format the retrieved chunks before passing them to the LLM? Describe the structure — not the code. Consider: will you label chunks by game? Include distance scores? Separate chunks with delimiters?*

```
I'll format as numbered chunks with explicit game labels:

[1] [Game: Catan]
When a 7 is rolled, no resources are produced...

[2] [Game: Catan]
The robber must be moved to a different terrain hex...

[3] [Game: Risk]
...

Each chunk:
- Numbered [1], [2], [3] for reference and clarity
- Labeled with [Game: XYZ] so the model knows which game each rule belongs to
- Separated by blank lines for readability
- NOT including distance scores (those are for debugging, not for the model)

This format makes it easy for the model to distinguish between games and cite correctly, while keeping the format clean and minimal.
```

---

### System prompt — grounding instruction

*Write the exact system prompt instruction you will use to prevent the model from answering beyond the retrieved text. This is the most important design decision in this function.*

```
You are RulesBot answering questions about board game rules using only retrieved rule text chunks.

ANSWER ONLY FROM RETRIEVED TEXT:
- Do not infer rules by analogy to other games you know
- Do not fill gaps with common sense about how games "should" work
- Do not reason about game balance, strategy, or design intent
- Do not answer "probably," "likely," or "I would guess"

IF THE ANSWER REQUIRES UNSTATED ASSUMPTIONS:
- Say clearly: "The rulebook doesn't explicitly state this."
- Example: If rules say "move to any hex" but don't specify whether you can stay put, say the rule is ambiguous — don't assume either way

CITE YOUR SOURCE EXACTLY:
- Quote the exact relevant phrase from the retrieved chunk in [brackets]
- State which game it comes from
- If answering from multiple chunks, cite each one

IF A CHUNK IS INCOMPLETE OR AMBIGUOUS:
- Don't complete it with logic
- Quote it back and label it as unclear or partial
- Say which parts aren't addressed in the loaded rules

WATCH FOR COMPOUND QUESTIONS:
- Break multi-part questions into parts
- Say clearly which parts the loaded rules cover and which they don't

RESPONSE FORMAT:
- Direct answer (if fully supported by chunks)
- Quote the exact rule text in [brackets]
- Name the game
- If not fully answerable: "This rule isn't covered in the loaded rule books"
- Never hedge with "probably," "I think," or "in my opinion"

If the user asks you to infer, analogize, or use external knowledge, respond:
"I can only answer from the loaded rulebooks. That question isn't covered in them."
```

---

### System prompt — citation instruction

*Write the exact instruction you will use to tell the model to identify which game its answer comes from.*

```
Always identify which game each rule comes from. When answering, cite the game name and quote the exact relevant phrase from the retrieved rule chunk in [brackets]. If your answer draws from multiple games, cite each one separately. Example: "[In Catan, when a 7 is rolled, every player with more than 7 cards discards half.]"
```

---

### Fallback behavior

*What should the response say when the answer isn't found in the loaded rule books? Write the exact fallback message.*

```
When retrieved_chunks is empty OR none of the chunks answer the question:

"I don't see this rule in the loaded rule books. The rule books I have loaded are: [list of loaded games]. Would you like to ask about a different rule, or rephrase your question?"

Do not attempt to answer using general knowledge. Do not say "I think this rule probably works this way." Only return the fallback message above.
```

---

### Handling low-relevance chunks

*`retrieved_chunks` may include chunks with high distance scores (weak relevance). Will you filter these out before building context, pass them all in, or handle them another way? What are the tradeoffs?*

```
Decision: Pass all retrieved chunks in, no filtering.

Rationale:
  - retrieve() has already ranked by relevance (distance score lowest first)
  - The LLM can see all the options and won't hallucinate if the first chunk
    doesn't answer the question — it can look at chunks [2] and [3]
  - Filtering risks removing a chunk that, while not the closest match, 
    actually contains the answer (e.g., if the question is phrased differently 
    than the rule section title)
  - The grounding instruction tells the model to say "not found" if none of 
    the chunks answer the question, so weak matches won't trick it into 
    answering incorrectly
  - Distance scores are not shown to the LLM (only games and text), so it 
    can't be confused by high distances

Tradeoff: The model has more text to search through, but this is safer than 
silently dropping potentially-useful chunks. If retrieval keeps returning 
irrelevant results, that's a chunking/embedding problem to fix upstream, not 
here.
```

---

### Message structure

*Describe how you will structure the messages list for the API call — what goes in the system message vs. the user message?*

```
System message:
- The grounding instruction (full text from above: "You are RulesBot...")
- The citation instruction (full text from above)

User message:
- A formatted context block with the retrieved chunks
- Then the user's original query

Format of the user message:

"You have been given the following rule text from loaded rule books:

[1] [Game: Catan]
When a 7 is rolled, no resources are produced...

[2] [Game: Catan]
The robber must be moved to a different terrain hex...

[3] [Game: Risk]
...

User question: What happens if you roll a 7 in Catan?"

This way:
- System message sets policy and behavior
- User message provides the actual context (chunks) and question
- The model has all the information it needs at once
- The context is clearly labeled and delimited
```

---

## Implementation Notes

*Fill this in after implementing and testing.*

**Test query and response:**

```
Query: [your test query]
Response: [abbreviated response]
Correctly grounded? [yes / no]
Cited the right game? [yes / no]
```

**One thing you changed from your original spec after seeing the actual output:**

```
[your answer here]
```
