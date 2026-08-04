"""
Task 5 — Semantic Search Module.

Viết module tìm kiếm ngữ nghĩa (dense retrieval) trên vector store.

Yêu cầu:
    - Input: query string + top_k
    - Output: danh sách chunks có score, sorted descending
    - Phải tương thích với embedding model và vector store ở Task 4
"""

from __future__ import annotations


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
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
    from .task4_chunking_indexing import embed_texts, get_collection

    # Bước 1: Embed query bằng cùng model ở Task 4 (text-embedding-3-small, L2-normalized)
    query_vector = embed_texts([query])[0]

    # Bước 2: Query vector store (cosine similarity)
    collection = get_collection()

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=min(top_k, collection.count()),  # tránh lỗi nếu DB ít hơn top_k
        include=["documents", "metadatas", "distances"],
    )

    # Bước 3: Chuyển kết quả, tính score và sắp xếp giảm dần
    output: list[dict] = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        # ChromaDB dùng cosine *distance* ∈ [0, 2]; chuyển sang similarity ∈ [0, 1]
        score = max(0.0, 1.0 - dist)
        output.append(
            {
                "content": doc,
                "score": round(score, 4),
                "metadata": meta,
            }
        )

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
