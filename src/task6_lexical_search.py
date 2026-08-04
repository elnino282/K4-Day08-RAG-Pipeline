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
    for doc, meta in zip(result["documents"], result["metadatas"]):
        corpus.append({"content": doc, "metadata": meta})
    return corpus


# ---------------------------------------------------------------------------
# Tokenizer đơn giản hỗ trợ tiếng Việt và tiếng Anh
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

    tokenized_corpus = [_tokenize(doc["content"]) for doc in corpus]
    bm25 = BM25Okapi(tokenized_corpus)
    return bm25


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def lexical_search(query: str, top_k: int = 10) -> list[dict]:
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
    import numpy as np

    bm25, corpus = _get_bm25_index()

    # Tokenize query theo cùng cách corpus
    tokenized_query = _tokenize(query)
    if not tokenized_query:
        return []

    scores = bm25.get_scores(tokenized_query)  # ndarray shape (N,)

    # Lấy top_k indices sắp xếp giảm dần
    top_indices = np.argsort(scores)[::-1][:top_k]

    results: list[dict] = []
    for idx in top_indices:
        if scores[idx] <= 0:
            break  # Các phần tử sau cũng ≤ 0, không có từ khớp
        results.append(
            {
                "content": corpus[idx]["content"],
                "score": round(float(scores[idx]), 4),
                "metadata": corpus[idx]["metadata"],
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
