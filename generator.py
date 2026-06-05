from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL

_client = Groq(api_key=GROQ_API_KEY)


def generate_response(query, retrieved_chunks):
    """
    Generate a grounded answer from retrieved rule chunks.

    TODO — Milestone 3:

    `retrieved_chunks` is the list returned by retrieve(). Each item is a dict:
      - "text"     : the chunk text
      - "game"     : the game name
      - "distance" : similarity score (you can use this to filter weak matches)

    Before writing code, talk through these with your group:
      - How will you format the chunks into a context block for the prompt?
      - What instructions will stop the model from answering beyond what the
        rules say? (Grounding is the whole point — a confident wrong answer
        is worse than an honest "I don't know.")
      - How will you surface which game each answer comes from?

    Your response should:
      1. Answer using only the retrieved context — not the model's general knowledge
      2. Make clear which game the answer comes from
      3. Say so clearly when the answer isn't in the loaded rules

    Return the response as a plain string.
    """
    if not retrieved_chunks:
        return (
            "I couldn't find anything relevant in the loaded rule books. "
            "Try rephrasing your question — or check that your ingestion pipeline is working."
        )

    # Format retrieved chunks into context block
    context_lines = ["You have been given the following rule text from loaded rule books:", ""]
    for i, chunk in enumerate(retrieved_chunks, 1):
        context_lines.append(f"[{i}] [Game: {chunk['game']}]")
        context_lines.append(chunk['text'])
        context_lines.append("")

    context_block = "\n".join(context_lines)

    # Build system message with grounding instruction and citation instruction
    system_message = """You are RulesBot answering questions about board game rules using only retrieved rule text chunks.

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

Always identify which game each rule comes from. When answering, cite the game name and quote the exact relevant phrase from the retrieved rule chunk in [brackets]."""

    # Build user message
    user_message = context_block + f"\nUser question: {query}"

    # Call Groq API
    response = _client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
    )

    return response.choices[0].message.content
