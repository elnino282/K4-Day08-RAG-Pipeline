"""
Task 6 — Lexical Search Module (BM25).

Mặc định sử dụng BM25. Nếu dùng phương pháp khác (TF-IDF, Elasticsearch,
Weaviate BM25 built-in), hãy giải thích cơ chế trong buổi demo → +5 bonus.

Cài đặt:
    pip install rank-bm25

BM25 hoạt động thế nào:
    - Term Frequency (TF): từ xuất hiện nhiều trong document → điểm cao
    - Inverse Document Frequency (IDF): từ hiếm → quan trọng hơn
    - Document length normalization: document dài không bị ưu tiên quá mức
    - Formula: score(q,d) = Σ IDF(qi) * (tf(qi,d) * (k1+1)) / (tf(qi,d) + k1*(1-b+b*|d|/avgdl))
    - k1=1.5 (term saturation), b=0.75 (length normalization)
"""

from __future__ import annotations

import re
from functools import lru_cache


# ---------------------------------------------------------------------------
# Corpus loading — lấy từ ChromaDB (tái sử dụng Task 4) để đồng nhất dữ liệu
# ---------------------------------------------------------------------------

def _load_corpus_from_chroma() -> list[dict]:
    """Lấy toàn bộ documents + metadata từ ChromaDB collection."""
    from .task4_chunking_indexing import get_collection

    collection = get_collection()
    total = collection.count()
    if total == 0:
        return []

    # ChromaDB get() có giới hạn mặc định 10 — cần truyền limit rõ ràng
    result = collection.get(
        limit=total,
        include=["documents", "metadatas"],
    )

    corpus: list[dict] = []
    for chunk_id, doc, meta in zip(
        result["ids"], result["documents"], result["metadatas"]
    ):
        metadata = dict(meta or {})
        metadata.setdefault("chunk_id", chunk_id)
        corpus.append({"content": doc, "metadata": metadata})
    return corpus


# ---------------------------------------------------------------------------
# Tokenizer đơn giản cho nội dung tiếng Việt
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> list[str]:
    """
    Tokenize text thành danh sách từ thường hóa.

    Dùng regex split để giữ nguyên tiếng Việt có dấu,
    loại bỏ ký tự đặc biệt và từ quá ngắn (1 ký tự).
    """
    text = text.lower()
    # Giữ lại chữ cái (kể cả Unicode/tiếng Việt), số; tách bằng mọi ký tự khác
    tokens = re.findall(r"[\w\u00C0-\u024F\u1EA0-\u1EF9]+", text)
    return [t for t in tokens if len(t) > 1]


def _searchable_text(document: dict) -> str:
    """Ghép nội dung với metadata mô tả để BM25 tìm được tên/chủ đề tài liệu."""
    metadata = document.get("metadata") or {}
    metadata_text = " ".join(
        str(metadata.get(field, ""))
        for field in ("title", "category", "source", "customer_role")
    )
    # Các metadata như ``order-tracking`` và đường dẫn dùng dấu phân cách;
    # đổi chúng thành khoảng trắng để query ``order tracking`` khớp từng từ.
    metadata_text = re.sub(r"[_\-/\\.]+", " ", metadata_text)
    return f"{document.get('content', '')} {metadata_text}".strip()


# ---------------------------------------------------------------------------
# BM25 index — build một lần, cache lại cho mọi lần gọi sau
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _get_bm25_index():
    """
    Trả về tuple (bm25_model, corpus) đã được cache.

    lru_cache đảm bảo BM25 chỉ được build một lần trong suốt
    vòng đời của process (quan trọng khi chạy trong Streamlit).
    """
    corpus = _load_corpus_from_chroma()
    if not corpus:
        raise ValueError(
            "Corpus rỗng — hãy chạy Task 4 để index dữ liệu vào ChromaDB trước."
        )
    bm25_model = build_bm25_index(corpus)
    return bm25_model, corpus


def build_bm25_index(corpus: list[dict]):
    """
    Xây dựng BM25 index từ corpus.

    Args:
        corpus: List of {'content': str, 'metadata': dict}

    Returns:
        BM25Okapi object đã được fit trên corpus.
    """
    from rank_bm25 import BM25Okapi

    tokenized_corpus = [_tokenize(_searchable_text(doc)) for doc in corpus]
    bm25 = BM25Okapi(tokenized_corpus)
    return bm25


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def lexical_search(
    query: str,
    top_k: int = 10,
    metadata_filter: dict | None = None,
) -> list[dict]:
    """
    Tìm kiếm từ khóa sử dụng BM25.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,      # BM25 score (normalized, ≥ 0)
            'metadata': dict
        }
        Sorted by score descending.
        Chỉ trả về các kết quả có score > 0 (có từ khóa khớp).
    """
    if not isinstance(query, str) or not query.strip() or top_k <= 0:
        return []

    bm25, corpus = _get_bm25_index()

    # Tokenize query theo cùng cách corpus
    tokenized_query = _tokenize(query)
    if not tokenized_query:
        return []

    scores = bm25.get_scores(tokenized_query)  # ndarray shape (N,)

    ranked: list[tuple[float, str, int]] = []
    for idx, raw_score in enumerate(scores):
        score = float(raw_score)
        metadata = corpus[idx]["metadata"]
        matches_filter = not metadata_filter or all(
            metadata.get(key) == value for key, value in metadata_filter.items()
        )
        if score > 0 and matches_filter:
            ranked.append((score, metadata["chunk_id"], idx))
    ranked.sort(key=lambda item: (-item[0], item[1]))

    results: list[dict] = []
    for score, _, idx in ranked[:top_k]:
        results.append(
            {
                "content": corpus[idx]["content"],
                "score": round(score, 6),
                "metadata": dict(corpus[idx]["metadata"]),
            }
        )

    return results


if __name__ == "__main__":
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    # Test
    results = lexical_search("phương thức thanh toán shopee", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
