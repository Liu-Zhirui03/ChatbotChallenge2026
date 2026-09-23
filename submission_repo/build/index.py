"""Indexer. STUB. Workshop 1 block 4.

Chunk the scraped text and write it to the store. Run this file
directly, after build/scrape.py, to (re)build data/chroma.

Store metadata now. Level 4 questions need to filter by year and page
type, and adding a field later means rebuilding everything.
"""
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot.store import add_to_store, get_store

CHUNK_SIZE, OVERLAP = 800, 100


def chunk(text: str, size: int = CHUNK_SIZE, overlap: int = OVERLAP,
          heading: str = "") -> list[str]:
    """Split section text with overlap and include its heading in each chunk.

    Overlap exists because a fact split across a boundary is lost: a
    date at char 998 and its event name at char 1002 land in different
    chunks and neither answers the question.

    """
    text = " ".join(text.split())
    if not text:
        return []
    heading = " ".join(heading.split())
    prefix = f"{heading}\n" if heading else ""
    body_size = size - len(prefix)
    if body_size <= overlap or overlap < 0:
        raise ValueError("chunk size must exceed heading length and overlap")
    step = body_size - overlap
    return [prefix + text[i:i + body_size] for i in range(0, len(text), step)]


def build_index(pages: list[dict], reset: bool = True):
    if not pages:
        raise ValueError("No pages to index; refusing to reset the existing index")
    texts, metas = [], []
    for page in pages:
        sections = page.get("sections") or [{"heading": "", "text": page["text"]}]
        position = 0
        for section in sections:
            for piece in chunk(section.get("text", ""),
                               heading=section.get("heading", "")):
                meta = {
                    "url": page["url"],
                    "title": page.get("title", ""),
                    "position": position,
                    "kind": "text",
                }
                if page.get("year") is not None:
                    meta["year"] = int(page["year"])
                if page.get("page_type"):
                    meta["page_type"] = str(page["page_type"])
                texts.append(piece)
                metas.append(meta)
                position += 1
    store = get_store(reset=reset)
    add_to_store(store, texts, metas)
    print(f"indexed {len(texts)} chunks")
    return store


if __name__ == "__main__":
    pages_path = Path("data/pages.json")
    if not pages_path.exists():
        raise SystemExit("Missing data/pages.json. Configure and run python build/scrape.py first.")
    pages = json.loads(pages_path.read_text())
    if not pages:
        raise SystemExit("data/pages.json contains no pages; refusing to reset the existing index.")
    build_index(pages)
