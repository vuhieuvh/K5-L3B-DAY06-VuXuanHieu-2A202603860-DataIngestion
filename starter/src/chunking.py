"""Two chunking strategies over the same normalized text."""
from uuid import NAMESPACE_URL, uuid5

from .models import Chunk, DocumentPage

SIZE = 500
OVERLAP = 50
MAX_SIZE = 800


def make_chunk(page: DocumentPage, strategy: str, start: int, end: int) -> Chunk:
    spans = [span for span in page.metadata["sections"] if span[1] > start and span[0] < end]
    chapters = sorted({span[2] for span in spans if span[2]})
    articles = sorted({span[3] for span in spans if span[3]})
    chunk_id = str(uuid5(NAMESPACE_URL, f"{page.document_id}/{strategy}/{page.page}/{start}/{end}"))
    return Chunk(chunk_id, page.document_id, page.source, page.page, page.text[start:end],
                 {"chapter": chapters, "article": articles, "start": start, "end": end})


def fixed_size(page: DocumentPage, size: int, overlap: int) -> list[Chunk]:
    if not 0 <= overlap < size:
        raise ValueError("Expected 0 <= overlap < size")
    chunks = []
    for start in range(0, len(page.text), size - overlap):
        end = min(start + size, len(page.text))
        chunks.append(make_chunk(page, "A", start, end))
        if end == len(page.text):
            break
    return chunks


def by_paragraph(page: DocumentPage, max_size: int) -> list[Chunk]:
    chunks = []
    start = end = 0
    previous_scope = None
    for left, right, chapter, article in page.metadata["sections"]:
        scope = chapter, article
        if end > start and (scope != previous_scope or right - start > max_size):
            chunks.append(make_chunk(page, "B", start, end))
            start = end = left
        while right - start > max_size:
            cut = page.text.rfind(" ", start + 1, start + max_size + 1)
            if cut < 0:
                cut = start + max_size
            chunks.append(make_chunk(page, "B", start, cut))
            start = cut + int(page.text[cut] == " ")
        end, previous_scope = right, scope
    if end > start:
        chunks.append(make_chunk(page, "B", start, end))
    return chunks

