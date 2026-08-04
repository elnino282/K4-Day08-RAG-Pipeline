"""
Task 9 — Retrieval Pipeline Hoàn Chỉnh.

Kết hợp semantic search + lexical search + reranking + PageIndex fallback
thành một pipeline thống nhất.

Logic:
    1. Chạy semantic_search + lexical_search song song
    2. Merge kết quả (RRF hoặc weighted fusion)
    3. Rerank
    4. Nếu top result score < threshold → fallback sang PageIndex
    5. Return top_k results

⚠️ BẪY THƯỜNG GẶP — đọc kỹ trước khi code:
    Nếu bạn dùng điểm RRF đã fuse (Task 7) để so với score_threshold, bạn sẽ gặp bug
    thật: RRF max score luôn ≈ 1/(k+1) ≈ 0.0164 (k=60) BẤT KỂ nội dung có liên quan
    hay không. Nếu đặt threshold thấp (như 0.005) để "hợp" với thang điểm RRF, thực
    chất KHÔNG câu hỏi nào đủ thấp để trigger fallback nữa — kể cả query hoàn toàn vô
    nghĩa vẫn trả về kết quả "hybrid" (rác) thay vì fallback đúng như thiết kế.

    Cách sửa đúng: giữ điểm cosine similarity GỐC của semantic_search (trước khi qua
    RRF) làm căn cứ quyết định fallback, tách biệt khỏi điểm RRF dùng để sắp xếp kết
    quả cuối cùng. Calibrate threshold bằng cách tự đo: chạy vài câu hỏi chắc chắn
    liên quan và vài câu chắc chắn lạc đề/rác qua semantic_search, xem khoảng cách
    điểm số giữa hai nhóm rồi chọn ngưỡng nằm giữa.
"""

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank_rrf
from .task8_pageindex_vectorless import pageindex_search


# =============================================================================
# CONFIGURATION
# =============================================================================

# TODO: Calibrate threshold này bằng cách tự đo điểm cosine của semantic_search
# cho câu hỏi liên quan vs câu hỏi lạc đề (xem ghi chú ở trên) — ĐỪNG copy nguyên
# giá trị mẫu, mỗi corpus/embedding model sẽ cho khoảng điểm khác nhau.
SCORE_THRESHOLD = 0.3   # Nếu best score (cosine gốc) < threshold → fallback PageIndex
DEFAULT_TOP_K = 5
RERANK_METHOD = "rrf"  # "cross_encoder" | "mmr" | "rrf"


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
) -> list[dict]:
    """
    Retrieval pipeline hoàn chỉnh với fallback logic.

    Pipeline:
        Query
          ├→ Semantic Search → dense_results (giữ điểm cosine gốc)
          ├→ Lexical Search  → sparse_results
          │
          ├→ Merge (RRF) → merged_results
          ├→ Rerank → reranked_results
          │
          └→ If dense_results[0]["score"] < threshold:
                └→ PageIndex Vectorless → fallback_results

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả cuối cùng
        score_threshold: Ngưỡng điểm cosine gốc tối thiểu (KHÔNG phải điểm RRF)
        use_reranking: Có áp dụng reranking hay không

    Returns:
        List of {
            'content': str,
            'score': float,
            'metadata': dict,
            'source': str  # 'hybrid' hoặc 'pageindex'
        }
    """
    # Validate input
    if not isinstance(query, str) or not query.strip():
        return []

    fetch_k = top_k * 3  # Lấy nhiều hơn để RRF có đủ candidates

    # -------------------------------------------------------------------------
    # Step 1: Chạy semantic search + lexical search
    #   - dense_results: điểm cosine GỐC, dùng để quyết định fallback ở Step 2
    #   - sparse_results: điểm BM25, dùng để RRF fusion ở Step 3
    # -------------------------------------------------------------------------
    dense_results = semantic_search(query, top_k=fetch_k)
    sparse_results = lexical_search(query, top_k=fetch_k)

    # -------------------------------------------------------------------------
    # Step 2: Kiểm tra fallback bằng điểm COSINE GỐC (trước khi RRF)
    #   ⚠ KHÔNG dùng điểm RRF để so threshold vì RRF max ≈ 1/(k+1) ≈ 0.016
    #   và không phản ánh mức độ liên quan thực sự của nội dung.
    # -------------------------------------------------------------------------
    best_cosine_score = dense_results[0]["score"] if dense_results else 0.0

    if best_cosine_score < score_threshold:
        print(
            f"  ⚠ Semantic best score ({best_cosine_score:.3f}) < threshold "
            f"({score_threshold}) → fallback sang PageIndex"
        )
        fallback = pageindex_search(query, top_k=top_k)
        if fallback:
            for item in fallback:
                item["source"] = "pageindex"
            return fallback[:top_k]
        # PageIndex cũng không trả kết quả — tiếp tục dùng hybrid tốt nhất có thể
        print("  ⚠ PageIndex không trả kết quả — dùng hybrid kết quả gốc")

    # -------------------------------------------------------------------------
    # Step 3: RRF Fusion — gộp dense + sparse thành một ranked list thống nhất
    # -------------------------------------------------------------------------
    lists_to_fuse = [lst for lst in [dense_results, sparse_results] if lst]

    if use_reranking and lists_to_fuse:
        merged = rerank_rrf(lists_to_fuse, top_k=fetch_k)
    else:
        # Không rerank: nối, dedup theo content, sắp xếp theo cosine score
        seen: set[str] = set()
        merged = []
        for item in sorted(
            dense_results + sparse_results,
            key=lambda x: x.get("score", 0.0),
            reverse=True,
        ):
            if item["content"] not in seen:
                seen.add(item["content"])
                merged.append(item)

    # -------------------------------------------------------------------------
    # Step 4: Gắn nhãn source = "hybrid" và trả kết quả
    # -------------------------------------------------------------------------
    for item in merged:
        item["source"] = "hybrid"

    return merged[:top_k]


if __name__ == "__main__":
    test_queries = [
        "What payment methods does Shopee support?",
        "How do I request a return or refund?",
        "What evidence do I need for a refund request?",
        "xyzabc123nonsense",  # Query không có kết quả → test fallback
    ]

    for q in test_queries:
        print(f"\nQuery: {q}")
        print("-" * 60)
        results = retrieve(q, top_k=3)
        for i, r in enumerate(results, 1):
            print(f"  {i}. [{r['score']:.3f}] [{r['source']}] {r['content'][:80]}...")
