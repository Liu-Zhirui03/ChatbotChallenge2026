"""Offline contract tests for indexing, image ingestion, and retrieval."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bot import answer  # noqa: E402
from build import images, index  # noqa: E402


class TextIndexTests(unittest.TestCase):
    def test_clean_metadata_and_stable_ids_are_indexed(self) -> None:
        document = {
            "id": "doc_123",
            "url": "https://example.com/workshop/",
            "site": "example.com",
            "title": "Workshop",
            "text": "Fallback text",
            "sections": [{"heading": "Details", "text": "Date: 1 January 2025"}],
            "year": 2025,
            "academic_year": "2024/25",
            "page_type": "event",
        }
        with patch.object(index, "get_store", return_value=object()), patch.object(
            index, "add_to_store"
        ) as add:
            index.build_index([document])

        texts, metadata = add.call_args.args[1:3]
        ids = add.call_args.kwargs["ids"]
        self.assertEqual(texts, ["Details\nDate: 1 January 2025"])
        self.assertEqual(metadata[0]["year"], 2025)
        self.assertEqual(metadata[0]["page_type"], "event")
        self.assertEqual(ids, ["txt_doc_123_0"])


class ImageIndexTests(unittest.TestCase):
    def test_descriptions_keep_document_metadata(self) -> None:
        image = {
            "src": "https://example.com/poster.jpg",
            "alt": "Workshop poster",
            "caption": "Robotics",
            "document_ids": ["doc_123"],
        }
        document = {
            "id": "doc_123", "url": "https://example.com/workshop/",
            "title": "Workshop", "year": 2025, "page_type": "event",
        }
        store = Mock()
        with patch.object(images, "get_store", return_value=store), patch.object(
            images, "add_to_store"
        ) as add:
            count = images.index_descriptions(
                {image["src"]: "Visible date: 1 January 2025."}, [image], [document]
            )

        self.assertEqual(count, 1)
        store.delete.assert_called_once_with(where={"kind": "image"})
        texts, metadata = add.call_args.args[1:3]
        self.assertIn("Visible date", texts[0])
        self.assertEqual(metadata[0]["kind"], "image")
        self.assertEqual(metadata[0]["year"], 2025)
        self.assertTrue(add.call_args.kwargs["ids"][0].startswith("img_"))

    def test_prompt_requests_ocr_counts_and_spatial_evidence(self) -> None:
        prompt = images.DESCRIPTION_PROMPT.casefold()
        for term in ("transcribe", "count", "spatial", "wall"):
            self.assertIn(term, prompt)
        self.assertNotIn("todo", prompt)


class AnswerTests(unittest.TestCase):
    def test_visual_year_filter_uses_chroma_types_and_and_operator(self) -> None:
        self.assertEqual(
            answer._metadata_where("What is shown in the 2025 picture?"),
            {"$and": [{"kind": "image"}, {"year": 2025}]},
        )

    def test_text_year_does_not_hide_undated_living_pages(self) -> None:
        self.assertIsNone(
            answer._metadata_where("What was the funding deadline in 2025-26?")
        )

    def test_empty_filtered_retrieval_falls_back(self) -> None:
        fallback = [{"text": "answer", "metadata": {}, "distance": 0.1}]
        with patch.object(answer, "retrieve", side_effect=[[], fallback]) as retrieve:
            result = answer._retrieve_safe("question", where={"kind": "image"})
        self.assertEqual(result, fallback)
        self.assertEqual(retrieve.call_count, 2)


if __name__ == "__main__":
    unittest.main()
