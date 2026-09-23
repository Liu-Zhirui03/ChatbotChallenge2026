"""Your chatbot. STUB. This is the file you actually write.

Two functions must exist with these exact names and signatures. Every
other line in this file, and every file under build/, is yours to
rewrite.
"""
import re
from typing import Optional

from bot.hybrid import hybrid_retrieve
from bot.llm import chat
from bot.store import get_store, query

# --------------------------------------------------------------------
# The prompt. Workshop 1 block 2 covers what each part is doing.
# --------------------------------------------------------------------
SYSTEM_PROMPT = """You answer questions about the Tam Wing Fan Innovation Wing.

Answer only from the context below. Where the context disagrees with
what you think you know, the context is correct.

Reply with the answer only. No explanation, no preamble. If the question
asks how many, reply with a number.

If the context does not contain the answer, give your best guess anyway.
Never reply that you do not know."""

CONFIG = {
    "k": 5,    # try 3 to 10, tuned in Workshop 1 block 5
    "wide_k": 50,
}


def _needs_split(question: str) -> bool:
    q = question.lower()
    return (
        " or " in q
        or " and " in q
        or "which two" in q
        or "longer" in q
        or "compare" in q
    )


def _subquestions(question: str) -> list[str]:
    out = chat([{
        "role": "user",
        "content": (
            "Split this into the separate factual questions needed to answer it. "
            "One per line, no numbering, no commentary. "
            "If it is already a single question, return it unchanged.\n\n"
            + question
        ),
    }], max_tokens=200)
    parts = [ln.strip(" -0123456789.") for ln in out.splitlines() if ln.strip()]
    return parts or [question]


def _wants_number(question: str) -> bool:
    q = question.lower()
    return any(w in q for w in (
        "how many", "how much", "what is the capacity",
        "capacity of", "in total",
    ))


def _as_number(reply: str) -> str:
    reply = reply.strip().strip("\"'`")
    if re.fullmatch(r"\d+(?:\.\d+)?", reply):
        return reply
    nums = re.findall(r"\d+(?:\.\d+)?", reply)
    last = reply.splitlines()[-1] if reply else ""
    last_nums = re.findall(r"\d+(?:\.\d+)?", last)
    if last_nums:
        return last_nums[-1]
    return nums[-1] if nums else reply


def _metadata_where(question: str) -> Optional[dict]:
    """Best-effort filter. Missing index fields make Chroma raise; caller
    must fall back to an unfiltered retrieve.
    """
    q = question.lower()
    filters: list[dict] = []
    visual = any(w in q for w in (
        "photo", "photograph", "image", "picture", "shown",
        "poster", "on the wall", "written on",
    ))
    if visual:
        filters.append({"kind": "image"})
    year = re.search(r"\b(20\d{2})\b", question)
    if year and visual:
        # index.py and images.py store Chroma years as integers. Chroma metadata
        # comparisons are type-sensitive, so a string silently misses matches.
        filters.append({"year": int(year.group(1))})
    if not filters:
        return None
    return filters[0] if len(filters) == 1 else {"$and": filters}


def _retrieve_safe(question: str, k: int = None, where: dict = None) -> list[dict]:
    try:
        chunks = retrieve(question, k=k, where=where)
        if chunks or not where:
            return chunks
    except Exception:
        pass
    return retrieve(question, k=k)


def _format_chunks(chunks: list[dict]) -> str:
    return "\n\n".join(
        f"[{c['metadata'].get('url', '?')}]\n{c['text']}" for c in chunks
    )


def retrieve(question: str, k: int = None, where: dict = None) -> list[dict]:
    """Return reranked dense + BM25 chunks most relevant to the question.

    Kept separate from rag_answer on purpose: it lets you check whether
    an answer was ever fetched at all, which is the only way to tell a
    retrieval failure from a prompt failure. Do not delete it even if
    you rewrite everything else.
    """
    requested = k or CONFIG["k"]
    pool_size = min(100, max(30, requested * 3))
    store = get_store()
    dense = query(store, question, k=pool_size, where=where)
    return hybrid_retrieve(question, dense, k=requested, where=where)


def rag_answer(question: str) -> str:
    """One question in, one answer out.

    Runs once per question with a 30 second budget. Anything expensive
    belongs in build/, not here.
    """
    where = _metadata_where(question)

    if _wants_number(question):
        chunks = _retrieve_safe(question, k=CONFIG["wide_k"], where=where)
        context = _format_chunks(chunks)
    elif _needs_split(question):
        blocks = []
        for i, part in enumerate(_subquestions(question), 1):
            found = _retrieve_safe(part, k=CONFIG["k"], where=where)
            blocks.append(f"[from sub-question {i}: {part}]\n{_format_chunks(found)}")
        context = "\n\n".join(blocks)
    else:
        chunks = _retrieve_safe(question, k=CONFIG["k"], where=where)
        context = _format_chunks(chunks)

    reply = chat([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
    ])

    reply = reply.strip()
    if _wants_number(question):
        return _as_number(reply)
    return reply


def rag_answer_batch(questions: list[str]) -> list[str]:
    """Many questions in, the same number of answers out, in order.

    Ships as a loop, which is correct and is all most teams will need.
    Replace it if you can share work across questions: one embedding
    call for every query rather than one per query, the store opened
    once, sub-queries running concurrently.

    Whatever you do, answers[i] must be the answer to questions[i].
    """
    return [rag_answer(q) for q in questions]
