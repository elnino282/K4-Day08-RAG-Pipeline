"""Task 4: chunk normalized Markdown documents and index them in ChromaDB."""

from __future__ import annotations

import argparse
import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
STANDARDIZED_DIR = PROJECT_ROOT / "data" / "standardized"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"

# Load environment variables from the project-level .env file.
load_dotenv(PROJECT_ROOT / ".env")

# Recursive splitting prefers Markdown paragraph boundaries and remains robust
# for documents without consistent headings. 800 characters retain useful
# context; 100-character overlap preserves statements at chunk boundaries.
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
CHUNKING_METHOD = "recursive"

# text-embedding-3-small (OpenAI) — 1536-dimension, multilingual, cost-efficient.
# Requires OPENAI_API_KEY to be set in the .env file.
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
# Number of chunks sent to the OpenAI Embeddings API in one request.
# OpenAI accepts up to 2048 inputs per call; 100 is safe and avoids timeouts.
_EMBED_BATCH_SIZE = 100

# ChromaDB provides a local persistent cosine-similarity vector store.
VECTOR_STORE = "chromadb"
COLLECTION_NAME = "ecommerce_support_docs"


def _infer_customer_role(document_path: Path) -> str:
    """Infer the audience label required by the K4 lab from its filename."""
    name = document_path.stem.lower()

    if any(keyword in name for keyword in ("listing", "seller", "nguoi-ban")):
        return "seller"

    if any(keyword in name for keyword in ("return", "refund", "buyer", "nguoi-mua")):
        return "buyer"

    return "both"


def load_documents() -> list[dict]:
    """Load non-empty Markdown files with source, type, and audience metadata."""
    if not STANDARDIZED_DIR.exists():
        return []

    documents: list[dict] = []

    for md_file in sorted(STANDARDIZED_DIR.rglob("*.md")):
        try:
            content = md_file.read_text(encoding="utf-8").strip()
        except UnicodeDecodeError as exc:
            raise ValueError(f"Không thể đọc file UTF-8: {md_file}") from exc

        if not content:
            continue

        doc_type = (
            md_file.parent.name
            if md_file.parent != STANDARDIZED_DIR
            else "unknown"
        )

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
    """Split documents into overlapping chunks while preserving metadata."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks: list[dict] = []

    for document in documents:
        content = document.get("content", "").strip()
        if not content:
            continue

        for index, chunk_text in enumerate(splitter.split_text(content)):
            chunks.append(
                {
                    "content": chunk_text,
                    "metadata": {
                        **document.get("metadata", {}),
                        "chunk_index": index,
                    },
                }
            )

    return chunks


@lru_cache(maxsize=1)
def get_openai_client():
    """Return a cached OpenAI client using OPENAI_API_KEY from the .env file."""
    from openai import OpenAI

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY chưa được cấu hình. "
            "Thêm OPENAI_API_KEY=sk-... vào file .env của dự án."
        )
    return OpenAI(api_key=api_key)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed một danh sách văn bản bằng OpenAI text-embedding-3-small.

    Gửi theo batch để tránh vượt giới hạn request size của API.
    Vector trả về đã được L2-normalize để tương thích với ChromaDB cosine space.
    """
    import math

    client = get_openai_client()
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), _EMBED_BATCH_SIZE):
        batch = texts[i : i + _EMBED_BATCH_SIZE]
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        # Sắp xếp theo index để đảm bảo thứ tự đúng
        sorted_data = sorted(response.data, key=lambda d: d.index)
        for item in sorted_data:
            vec = item.embedding
            # L2 normalize — OpenAI trả raw vectors, ChromaDB cosine cần unit vectors
            norm = math.sqrt(sum(v * v for v in vec)) or 1.0
            all_embeddings.append([v / norm for v in vec])

    return all_embeddings


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Add normalized OpenAI text-embedding-3-small embeddings to every chunk."""
    if not chunks:
        return []

    texts = [chunk["content"] for chunk in chunks]
    print(f"   Embedding {len(texts)} chunks via OpenAI API...", flush=True)
    embeddings = embed_texts(texts)

    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding

    return chunks


def get_chroma_client():
    """Create the persistent ChromaDB client."""
    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def get_collection():
    """Open the existing persistent ChromaDB collection."""
    client = get_chroma_client()
    return client.get_collection(COLLECTION_NAME)


def collection_exists_and_has_data() -> bool:
    """Return True when the target collection exists and contains vectors."""
    from chromadb.errors import NotFoundError

    client = get_chroma_client()

    try:
        collection = client.get_collection(COLLECTION_NAME)
        return collection.count() > 0
    except NotFoundError:
        return False


def index_to_vectorstore(chunks: list[dict]):
    """Replace the Chroma collection with the supplied embedded chunks."""
    from chromadb.errors import NotFoundError

    if not chunks:
        raise ValueError("Không có chunk để index.")

    if any("embedding" not in chunk for chunk in chunks):
        raise ValueError("Mỗi chunk phải có embedding trước khi index.")

    client = get_chroma_client()

    try:
        client.delete_collection(COLLECTION_NAME)
    except NotFoundError:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    collection.add(
        ids=[
            (
                f"{chunk['metadata']['source']}"
                f"::chunk::{chunk['metadata']['chunk_index']}"
            )
            for chunk in chunks
        ],
        documents=[chunk["content"] for chunk in chunks],
        embeddings=[chunk["embedding"] for chunk in chunks],
        metadatas=[chunk["metadata"] for chunk in chunks],
    )

    return collection


def run_pipeline(force_reindex: bool = False) -> None:
    """Run load -> chunk -> embed -> persistent ChromaDB index."""
    print("=" * 58)
    print("Task 4: Chunking & Indexing")
    print(
        f"  Chunking: {CHUNKING_METHOD} "
        f"(size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})"
    )
    print(f"  Embedding: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    print(f"  Vector Store: {VECTOR_STORE}")
    print(f"  Chroma path: {CHROMA_DIR}")
    print("=" * 58)

    if not force_reindex and collection_exists_and_has_data():
        collection = get_collection()
        print("ChromaDB đã có dữ liệu.")
        print(f"Hiện có {collection.count()} chunks.")
        print("Bỏ qua chunking và embedding.")
        print("Dùng --force khi muốn index lại dữ liệu.")
        return

    print("1. Loading standardized Markdown documents...", flush=True)
    documents = load_documents()

    if not documents:
        raise FileNotFoundError(
            "Không tìm thấy tài liệu Markdown trong thư mục: "
            f"{STANDARDIZED_DIR}"
        )

    print(f"   Loaded {len(documents)} documents", flush=True)

    print("2. Chunking documents...", flush=True)
    chunks = chunk_documents(documents)

    if not chunks:
        raise ValueError("Không tạo được chunk từ tài liệu đầu vào.")

    print(f"   Created {len(chunks)} chunks", flush=True)

    print("3. Creating embeddings...", flush=True)
    embedded_chunks = embed_chunks(chunks)
    print(f"   Embedded {len(embedded_chunks)} chunks", flush=True)

    print("4. Writing vectors to ChromaDB...", flush=True)
    collection = index_to_vectorstore(embedded_chunks)

    print("=" * 58)
    print("Task 4 completed successfully.")
    print(f"Loaded documents: {len(documents)}")
    print(f"Indexed chunks: {collection.count()}")
    print(f"Collection: {COLLECTION_NAME}")
    print(f"Database path: {CHROMA_DIR}")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Chunk standardized Markdown documents and index them in ChromaDB."
        )
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Xóa collection hiện tại và index lại toàn bộ dữ liệu.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(force_reindex=args.force)