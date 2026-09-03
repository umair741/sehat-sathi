import re
from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

PDF_PATH = "data/health_docs/Sehat_Sathi_Health_Knowledge_Base.pdf"


SKIP_PAGES = {0, 1}  # Title page and Table of Contents


def load_pdf(path: str):
    reader = PdfReader(path)
    docs = []
    for i, page in enumerate(reader.pages):
        if i in SKIP_PAGES:
            continue
        docs.append(Document(
            page_content=page.extract_text(),
            metadata={"source": path, "page": i}
        ))
    print(f"Loaded {len(docs)} pages from {path} (skipped pages {SKIP_PAGES})")
    return docs


def chunking(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", "! ", "? ", "۔", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    print(f"Split into {len(chunks)} chunks")
    return chunks


def extract_page_sources(docs):
    """
    Scan each page for 'Source:' attribution and build a page -> source map.
    If a page has no source, carry forward the last known source.
    """
    source_pattern = re.compile(r"Source:\s*(.+)", re.IGNORECASE)
    page_sources = {}
    last_source = ""

    for doc in docs:
        page = doc.metadata["page"]
        match = source_pattern.search(doc.page_content)
        if match:
            last_source = match.group(1).strip()
        page_sources[page] = last_source

    return page_sources


def attach_metadata(chunks, page_sources):
    """
    Attach to every chunk:
      - source_file: the PDF file path
      - verified_source: WHO, CDC, MedlinePlus etc. (from its page)
    """
    for chunk in chunks:
        page = chunk.metadata.get("page", 0)
        chunk.metadata["source_file"] = PDF_PATH
        chunk.metadata["verified_source"] = page_sources.get(page, "")

    return chunks


if __name__ == "__main__":
    docs = load_pdf(PDF_PATH)
    page_sources = extract_page_sources(docs)
    chunks = chunking(docs)
    chunks = attach_metadata(chunks, page_sources)

    print(f"\n=== Total chunks: {len(chunks)} ===\n")
    for i, chunk in enumerate(chunks[:3]):
        print(f"--- Chunk {i+1} | page {chunk.metadata['page']} | {len(chunk.page_content)} chars ---")
        print(f"Source file: {chunk.metadata['source_file']}")
        print(f"Verified source: {chunk.metadata['verified_source']}")
        print(f"Content:\n{chunk.page_content[:200]}")
        print()

