from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

DATA_DIR = "data/health_docs"


def load_files(folder: str):
    loader = DirectoryLoader(
        folder,
        glob="**/*.{md,txt}",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    docs = loader.load()
    for doc in docs:
        print(f"Loaded: {doc.metadata['source']} ({len(doc.page_content)} chars)")
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


if __name__ == "__main__":
    docs = load_files(DATA_DIR)
    print(f"\nTotal files loaded: {len(docs)}")

    chunks = chunking(docs)
    print(f"\nFirst chunk preview:\n{chunks[0].page_content[:200]}")
