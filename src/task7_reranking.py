"""Task 7: hợp nhất thứ hạng bằng RRF và rerank tùy chọn qua Jina API."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import requests
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

JINA_RERANK_URL = "https://api.jina.ai/v1/rerank"
JINA_RERANK_MODEL = "jina-reranker-v2-base-multilingual"
JINA_TIMEOUT_SECONDS = 30
RRF_K = 60

LOGGER = logging.getLogger(__name__)


def _copy_candidate(candidate: dict) -> dict:
    """Sao chép candidate mà không sửa dữ liệu đầu vào của ranker trước."""
    copied = dict(candidate)
    copied["metadata"] = dict(candidate.get("metadata") or {})
    return copied


def _candidate_key(candidate: dict) -> str:
    """Tạo khóa ổn định để nhận diện cùng một chunk giữa Dense và BM25."""
    metadata = candidate.get("metadata") or {}
    chunk_id = metadata.get("chunk_id")
    if chunk_id:
        return str(chunk_id)

    source = metadata.get("source")
    chunk_index = metadata.get("chunk_index")
    if source is not None and chunk_index is not None:
        return f"{source}::chunk::{chunk_index}"

    # Tương thích với candidates đơn giản trong test hoặc demo.
    return str(candidate.get("content", ""))


def _numeric_score(candidate: dict) -> float | None:
    """Đọc score nếu có thể chuyển an toàn sang số thực."""
    try:
        return float(candidate["score"])
    except (KeyError, TypeError, ValueError):
        return None


def rerank_rrf(
    ranked_lists: list[list[dict]], top_k: int = 5, k: int = RRF_K
) -> list[dict]:
    """Gộp nhiều bảng xếp hạng bằng Reciprocal Rank Fusion.

    ``RRF(d) = sum(1 / (k + rank_r(d)))``. Điểm gốc của Dense/BM25
    được giữ riêng để Task 9 có thể quyết định fallback bằng cosine score.
    """
    if top_k <= 0 or not ranked_lists:
        return []
    if k < 0:
        raise ValueError("Hằng số k của RRF phải >= 0.")

    fused: dict[str, dict] = {}
    ranker_names = ("dense", "bm25")

    for list_index, ranked_list in enumerate(ranked_lists):
        ranker_name = (
            ranker_names[list_index]
            if list_index < len(ranker_names)
            else f"ranker_{list_index + 1}"
        )
        seen_in_list: set[str] = set()

        for rank, candidate in enumerate(ranked_list, start=1):
            key = _candidate_key(candidate)
            if not key or key in seen_in_list:
                continue
            seen_in_list.add(key)

            if key not in fused:
                item = _copy_candidate(candidate)
                item["rrf_score"] = 0.0
                item["best_rank"] = rank
                item["rerank_method"] = "rrf"
                fused[key] = item

            item = fused[key]
            item["rrf_score"] += 1.0 / (k + rank)
            item["best_rank"] = min(item["best_rank"], rank)
            item[f"{ranker_name}_rank"] = rank
            original_score = _numeric_score(candidate)
            if original_score is not None:
                item[f"{ranker_name}_score"] = original_score

    results = list(fused.values())
    for item in results:
        item["rrf_score"] = round(float(item["rrf_score"]), 12)
        item["score"] = item["rrf_score"]

    results.sort(
        key=lambda item: (
            -item["rrf_score"],
            item["best_rank"],
            _candidate_key(item),
        )
    )
    return results[:top_k]


def _rrf_fallback(candidates: list[dict], top_k: int) -> list[dict]:
    """Trả nguyên thứ hạng RRF khi Jina không sẵn sàng."""
    fallback = []
    for candidate in candidates[: max(0, top_k)]:
        item = _copy_candidate(candidate)
        item["rerank_method"] = "rrf_fallback"
        fallback.append(item)
    return fallback


def rerank_cross_encoder(
    query: str,
    candidates: list[dict],
    top_k: int = 5,
) -> list[dict]:
    """Rerank candidates bằng Jina; lỗi bất kỳ sẽ trả thứ hạng RRF đầu vào."""
    if not isinstance(query, str) or not query.strip() or top_k <= 0:
        return []
    if not candidates:
        return []

    api_key = os.getenv("JINA_API_KEY", "").strip()
    if not api_key:
        LOGGER.warning("Thiếu JINA_API_KEY; dùng kết quả RRF.")
        return _rrf_fallback(candidates, top_k)

    try:
        response = requests.post(
            JINA_RERANK_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": JINA_RERANK_MODEL,
                "query": query.strip(),
                "documents": [str(item.get("content", "")) for item in candidates],
                "top_n": min(top_k, len(candidates)),
                "return_documents": False,
            },
            timeout=JINA_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
        raw_results = payload.get("results")
        if not isinstance(raw_results, list) or not raw_results:
            raise ValueError("Jina không trả về danh sách results hợp lệ.")

        output: list[dict] = []
        seen_indices: set[int] = set()
        for result in raw_results:
            index = int(result["index"])
            if index < 0 or index >= len(candidates) or index in seen_indices:
                raise ValueError("Jina trả về candidate index không hợp lệ.")
            seen_indices.add(index)

            jina_score = float(result["relevance_score"])
            item = _copy_candidate(candidates[index])
            item["pre_rerank_score"] = item.get("score")
            item["jina_score"] = jina_score
            item["score"] = jina_score
            item["rerank_method"] = "jina"
            output.append(item)

        output.sort(key=lambda item: item["jina_score"], reverse=True)
        return output[:top_k]
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else "unknown"
        LOGGER.warning("Jina HTTP %s; dùng kết quả RRF.", status_code)
        return _rrf_fallback(candidates, top_k)
    except (KeyError, TypeError, ValueError, requests.RequestException) as exc:
        LOGGER.warning("Jina rerank lỗi (%s); dùng kết quả RRF.", type(exc).__name__)
        return _rrf_fallback(candidates, top_k)


def rerank_hybrid(
    query: str,
    ranked_lists: list[list[dict]],
    top_k: int = 5,
    candidate_pool_size: int = 20,
    use_jina: bool = True,
) -> list[dict]:
    """Flow Task 7: Dense + BM25 -> RRF -> Jina, lỗi Jina -> RRF."""
    if top_k <= 0:
        return []

    pool_size = max(top_k, candidate_pool_size)
    rrf_results = rerank_rrf(ranked_lists, top_k=pool_size)
    if not use_jina or not rrf_results:
        return rrf_results[:top_k]
    return rerank_cross_encoder(query, rrf_results, top_k=top_k)


def rerank_mmr(
    query_embedding: list[float],
    candidates: list[dict],
    top_k: int = 5,
    lambda_param: float = 0.7,
) -> list[dict]:
    """MMR không nằm trong flow mặc định của bài lab."""
    raise NotImplementedError("Task 7 sử dụng RRF kết hợp Jina, không sử dụng MMR.")


def rerank(
    query: str,
    candidates: list[dict],
    top_k: int = 5,
    method: str = "rrf",
) -> list[dict]:
    """Giao diện rerank chung, tương thích với template và Task 9."""
    if method in {"cross_encoder", "jina", "rrf_jina"}:
        return rerank_cross_encoder(query, candidates, top_k)
    if method == "rrf":
        return rerank_rrf([candidates], top_k=top_k)
    if method == "mmr":
        raise NotImplementedError("Hãy gọi rerank_mmr với query_embedding.")
    raise ValueError(f"Phương pháp rerank không hợp lệ: {method}")


if __name__ == "__main__":
    dense_demo = [
        {"content": "Chính sách trả hàng và hoàn tiền.", "score": 0.82, "metadata": {"chunk_id": "a"}},
        {"content": "Quy định đăng bán sản phẩm.", "score": 0.65, "metadata": {"chunk_id": "b"}},
    ]
    bm25_demo = [
        {"content": "Quy định đăng bán sản phẩm.", "score": 6.2, "metadata": {"chunk_id": "b"}},
        {"content": "Chính sách trả hàng và hoàn tiền.", "score": 4.1, "metadata": {"chunk_id": "a"}},
    ]
    for result in rerank_hybrid(
        "quy định trả hàng", [dense_demo, bm25_demo], top_k=2
    ):
        print(f"[{result['score']:.4f}] [{result['rerank_method']}] {result['content']}")
