"""Extract regulation pages and preserve chapter and article boundaries."""
import re
import unicodedata
from pathlib import Path

import fitz

from .models import DocumentPage

CHAPTER = re.compile(r"Chương ([IVX]+)$")
ARTICLE = re.compile(r"Điều (\d+)\.")
BOUNDARY = re.compile(r"^(?:Chương [IVX]+$|Điều \d+\.|\d+[.)]\s|[a-zđ]\)\s|[-–+]\s)")


def normalize_text(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", text).split())


def load_pdf(path: Path, document_id: str, source: str) -> list[DocumentPage]:
    pages = []
    chapter, article = "", 0
    with fitz.open(path) as pdf:
        for number, page in enumerate(pdf, 1):
            lines = [normalize_text(line) for line in page.get_text().splitlines()]
            if number > 1 and lines[0] == str(number):
                lines.pop(0)
            paragraphs = []
            spans = []
            for line in filter(None, lines):
                heading = CHAPTER.fullmatch(line)
                clause = ARTICLE.match(line)
                if heading or clause:
                    if heading:
                        chapter, article = heading[1], 0
                    else:
                        article = int(clause[1])
                if not paragraphs or BOUNDARY.match(line):
                    paragraphs.append(line)
                    spans.append((chapter, article))
                else:
                    paragraphs[-1] += " " + line
            if not paragraphs or not chapter:
                raise ValueError(f"Cannot extract physical page {number}")
            text = normalize_text(" ".join(paragraphs))
            sections = []
            start = 0
            for paragraph, (label, item) in zip(paragraphs, spans, strict=True):
                end = start + len(paragraph)
                sections.append((start, end, label, item))
                start = end + 1
            pages.append(DocumentPage(document_id, source, number, text, {"sections": sections}))
    return pages

