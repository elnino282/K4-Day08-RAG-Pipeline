"""
Task 5 — Semantic Search Module.

Viết module tìm kiếm ngữ nghĩa (dense retrieval) trên vector store.

Yêu cầu:
    - Input: query string + top_k
    - Output: danh sách chunks có score, sorted descending
    - Phải tương thích với embedding model và vector store ở Task 4
"""

from __future__ import annotations


def _cosine_distance_to_score(distance: float) -> float:
    """Đổi cosine distance của Chroma thành similarity trong khoảng [0, 1]."""
    return max(0.0, min(1.0, 1.0 - float(distance)))


def semantic_search(
    query: str,
    top_k: int = 10,
    metadata_filter: dict | None = None,
    include_embeddings: bool = True,
) -> list[dict]:
    """
    Tìm kiếm ngữ nghĩa sử dụng vector similarity.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,      # Nội dung chunk
            'score': float,      # Cosine similarity score
            'metadata': dict     # source, doc_type, chunk_index
        }
        Sorted by score descending.
    """
    if not isinstance(query, str) or not query.strip() or top_k <= 0:
        return []

    from chromadb.errors import NotFoundError
    from .task4_chunking_indexing import embed_texts, get_collection

    # Bước 1: Embed query bằng cùng model ở Task 4 (text-embedding-3-small, L2-normalized)
    query_vector = embed_texts([query.strip()])[0]

    # Bước 2: Query vector store (cosine similarity)
    try:
        collection = get_collection()
    except (NotFoundError, ValueError):
        return []

    collection_size = collection.count()
    if collection_size == 0:
        return []

    include = ["documents", "metadatas", "distances"]
    if include_embeddings:
        include.append("embeddings")
    query_kwargs = {
        "query_embeddings": [query_vector],
        "n_results": min(top_k, collection_size),
        "include": include,
    }
    if metadata_filter:
        query_kwargs["where"] = metadata_filter
    results = collection.query(**query_kwargs)

    # Bước 3: Chuyển kết quả, tính score và sắp xếp giảm dần
    output: list[dict] = []
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    ids = results.get("ids", [[]])[0]
    raw_embeddings = results.get("embeddings")
    embeddings = raw_embeddings[0] if raw_embeddings is not None else None

    for index, document in enumerate(documents):
        metadata = dict(metadatas[index] or {})
        metadata.setdefault("chunk_id", ids[index])
        item = {
            "content": document,
            "score": round(_cosine_distance_to_score(distances[index]), 6),
            "metadata": metadata,
        }
        if embeddings is not None:
            item["embedding"] = embeddings[index].tolist()
        output.append(item)

    output.sort(key=lambda x: x["score"], reverse=True)
    return output[:top_k]


if __name__ == "__main__":
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    # Test
    results = semantic_search("quy định trả hàng hoàn tiền shopee", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
