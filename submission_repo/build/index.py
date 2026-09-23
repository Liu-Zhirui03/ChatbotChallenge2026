"""Build the text index from the reviewed, cleaned web corpus.

Run this file after ``build/clean.py`` to recreate ``data/chroma``.

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
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS_PATH = PROJECT_ROOT / "data" / "processed" / "documents.json"


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
                    "document_id": page.get("id", ""),
                    "site": page.get("site", ""),
                }
                if section.get("heading"):
                    meta["section"] = str(section["heading"])
                if page.get("year") is not None:
                    meta["year"] = int(page["year"])
                if page.get("academic_year"):
                    meta["academic_year"] = str(page["academic_year"])
                if page.get("page_type"):
                    meta["page_type"] = str(page["page_type"])
                texts.append(piece)
                metas.append(meta)
                position += 1
    store = get_store(reset=reset)
    ids = [
        f"txt_{meta.get('document_id') or number}_{meta['position']}"
        for number, meta in enumerate(metas)
    ]
    add_to_store(store, texts, metas, ids=ids)
    print(f"indexed {len(texts)} chunks")
    return store


if __name__ == "__main__":
    if not DOCUMENTS_PATH.exists():
        raise SystemExit(
            "Missing data/processed/documents.json. Run python build/clean.py first."
        )
    pages = json.loads(DOCUMENTS_PATH.read_text(encoding="utf-8"))
    if not pages:
        raise SystemExit(
            "data/processed/documents.json contains no documents; "
            "refusing to reset the existing index."
        )
    build_index(pages)
