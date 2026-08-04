"""Task 4: chunk normalized Markdown documents and index them in ChromaDB."""

from functools import lru_cache
from pathlib import Path


STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

# Recursive splitting prefers Markdown paragraph boundaries and remains robust
# for documents without consistent headings. 800 characters retain useful
# context; 100-character overlap preserves statements at chunk boundaries.
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
CHUNKING_METHOD = "recursive"

# BGE-M3 is multilingual (Vietnamese and English) and produces 1024-dimension
# embeddings, so the same model can be used for documents and later queries.
EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DIM = 1024

# ChromaDB provides a local persistent cosine-similarity vector store.
VECTOR_STORE = "chromadb"
COLLECTION_NAME = "ecommerce_support_docs"


def _infer_customer_role(document_path: Path) -> str:
    """Infer the audience label used by the GameTFT knowledge base."""
    name = document_path.stem.lower()
    if any(keyword in name for keyword in ("developer", "brand", "policy")):
        return "developer"
    if any(keyword in name for keyword in ("competitive", "compete", "esports", "rules")):
        return "competitive-player"
    return "both"


def load_documents() -> list[dict]:
    """Load non-empty Markdown files with source, type, and audience metadata."""
    if not STANDARDIZED_DIR.exists():
        return []

    documents = []
    for md_file in sorted(STANDARDIZED_DIR.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8").strip()
        if not content:
            continue

        doc_type = md_file.parent.name if md_file.parent != STANDARDIZED_DIR else "unknown"
        documents.append(
            {
                "content": content,
                "metadata": {
                    "source": md_file.relative_to(STANDARDIZED_DIR).as_posix(),
                    "type": doc_type,
                    "customer_role": _infer_customer_role(md_file),
                },
            }
        )
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Split documents into overlapping chunks while preserving source metadata."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = []
    for document in documents:
        content = document.get("content", "").strip()
        if not content:
            continue
        for index, chunk_text in enumerate(splitter.split_text(content)):
            chunks.append(
                {
                    "content": chunk_text,
                    "metadata": {**document.get("metadata", {}), "chunk_index": index},
                }
            )
    return chunks


@lru_cache(maxsize=1)
def get_embedding_model():
    """Load BGE-M3 once so indexing and semantic search share one model."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL)


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Add normalized BGE-M3 embeddings to every chunk."""
    if not chunks:
        return []

    embeddings = get_embedding_model().encode(
        [chunk["content"] for chunk in chunks],
        show_progress_bar=True,
        normalize_embeddings=True,
    )
    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding.tolist()
    return chunks


def get_collection():
    """Open the persistent collection for the dense retrieval task."""
    import chromadb

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_collection(COLLECTION_NAME)


def index_to_vectorstore(chunks: list[dict]):
    """Replace the Chroma collection with the supplied embedded chunks."""
    if not chunks:
        raise ValueError("Khong co chunk de index.")
    if any("embedding" not in chunk for chunk in chunks):
        raise ValueError("Moi chunk phai co embedding truoc khi index.")

    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        client.delete_collection(COLLECTION_NAME)
    except ValueError:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    collection.add(
        ids=[
            f"{chunk['metadata']['source']}::chunk::{chunk['metadata']['chunk_index']}"
            for chunk in chunks
        ],
        documents=[chunk["content"] for chunk in chunks],
        embeddings=[chunk["embedding"] for chunk in chunks],
        metadatas=[chunk["metadata"] for chunk in chunks],
    )
    return collection


def run_pipeline():
    """Run load -> chunk -> embed -> persistent ChromaDB index."""
    print("=" * 50)
    print("Task 4: Chunking & Indexing")
    print(f"  Chunking: {CHUNKING_METHOD} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print(f"  Embedding: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    print(f"  Vector Store: {VECTOR_STORE}")
    print("=" * 50)

    documents = load_documents()
    chunks = chunk_documents(documents)
    embedded_chunks = embed_chunks(chunks)
    collection = index_to_vectorstore(embedded_chunks)

    print(f"Loaded {len(documents)} documents")
    print(f"Created and indexed {collection.count()} chunks")


if __name__ == "__main__":
    run_pipeline()
