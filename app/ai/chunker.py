from docling.chunking import HybridChunker

from docling_core.types import DoclingDocument

from typing import TypedDict



class ParentChunk(TypedDict):
    text: str
    heading: str | None
    page_number: int
    parent_index: int


class ChildChunk(TypedDict):
    text: str
    page_number: int
    parent_index: int
    child_index: int



hybrid_chunker = HybridChunker()



def get_chunk_page(chunk) -> int:
    for item in chunk.meta.doc_items:
        if item.prov:
            return item.prov[0].page_no

    return 1



def get_chunk_heading(chunk) -> str | None:
    headings = chunk.meta.headings

    if not headings:
        return None

    return " > ".join(headings)


# Chunk Document: Parent Child chunks based on heading & page number.


def chunk_document(
    document: DoclingDocument
) -> tuple[list[ParentChunk], list[ChildChunk]]:

    docling_chunks = list(
        hybrid_chunker.chunk(dl_doc=document)
    )

    grouped_chunks: dict[tuple[int, str | None], list] = {}

    for chunk in docling_chunks:

        page_number = get_chunk_page(chunk)

        heading = get_chunk_heading(chunk)

        key = (page_number, heading)

        grouped_chunks.setdefault(key, []).append(chunk)

    parents: list[ParentChunk] = []

    children: list[ChildChunk] = []

    for parent_index, ((page_number, heading), section_chunks) in enumerate(grouped_chunks.items(), start=1):

        parent_text = "\n\n".join(chunk.text for chunk in section_chunks)

        parents.append(
            {
                "text": parent_text,
                "heading": heading,
                "page_number": page_number,
                "parent_index": parent_index,
            }
        )

        for child_index, chunk in enumerate(section_chunks, start=1):

            child_text = (
                hybrid_chunker.contextualize(chunk)
            )

            children.append(
                {
                    "text": child_text,
                    "page_number": page_number,
                    "parent_index": parent_index,
                    "child_index": child_index,
                }
            )

    return parents, children