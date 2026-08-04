"""
Task 10 — Generation Có Citation.

Hướng dẫn:
    1. Chọn top_k, top_p phù hợp (giải thích lý do)
    2. Sắp xếp lại chunks sau reranking để tránh "lost in the middle"
    3. Inject context vào prompt
    4. Yêu cầu LLM trả lời có citation
    5. Nếu không đủ evidence → "I cannot verify this information"

Gợi ý LLM: OpenRouter có nhiều model gắn hậu tố ":free" không tính phí — xem
https://openrouter.ai/models?max_price=0 — phù hợp nếu chưa có credit trả phí.
Base URL: "https://openrouter.ai/api/v1", dùng chung interface với OpenAI SDK.
"""

import os
from dotenv import load_dotenv

load_dotenv()

from .task9_retrieval_pipeline import retrieve


# =============================================================================
# CONFIGURATION — Giải thích lựa chọn
# =============================================================================

# top_k: Số chunks đưa vào context
# Chọn 5 vì: đủ evidence mà không quá dài gây lost in the middle
TOP_K = 5

# top_p (nucleus sampling): Xác suất tích luỹ cho token generation
# Chọn 0.9 vì: đủ diverse nhưng không quá random
TOP_P = 0.9

# temperature: Độ ngẫu nhiên của output
# Chọn 0.3 vì: RAG cần factual, ít sáng tạo
TEMPERATURE = 0.3

# Provider chain: dùng cái nào có key, hết quota thì tự lùi sang cái kế tiếp.
# Cả 3 đều nói được giao thức OpenAI Chat Completions nên chỉ cần 1 SDK.
LLM_MODEL = "openai/gpt-4o-mini"  # model ID phía OpenRouter (nếu có key)
OPENAI_MODEL = "gpt-4o-mini"
GEMINI_OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


def _llm_providers() -> list[dict]:
    """Trả về danh sách provider khả dụng theo thứ tự ưu tiên."""
    providers = []

    if os.getenv("OPENROUTER_API_KEY"):
        providers.append({
            "name": "openrouter",
            "api_key": os.getenv("OPENROUTER_API_KEY"),
            "base_url": "https://openrouter.ai/api/v1",
            "model": LLM_MODEL,
        })

    if os.getenv("OPENAI_API_KEY"):
        providers.append({
            "name": "openai",
            "api_key": os.getenv("OPENAI_API_KEY"),
            "base_url": None,  # endpoint mặc định của OpenAI
            "model": OPENAI_MODEL,
        })

    if os.getenv("GEMINI_API_KEY"):
        providers.append({
            "name": "gemini",
            "api_key": os.getenv("GEMINI_API_KEY"),
            "base_url": GEMINI_OPENAI_BASE_URL,
            "model": os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        })

    return providers


def _call_llm(messages: list[dict]) -> str:
    """Gọi LLM qua provider đầu tiên chạy được; lỗi thì lùi sang provider sau."""
    from openai import OpenAI

    providers = _llm_providers()
    if not providers:
        raise EnvironmentError(
            "Chưa có LLM API key nào. Thêm OPENROUTER_API_KEY, OPENAI_API_KEY "
            "hoặc GEMINI_API_KEY vào file .env."
        )

    errors = []
    for provider in providers:
        try:
            client_kwargs = {"api_key": provider["api_key"]}
            if provider["base_url"]:
                client_kwargs["base_url"] = provider["base_url"]
            client = OpenAI(**client_kwargs)

            response = client.chat.completions.create(
                model=provider["model"],
                messages=messages,
                temperature=TEMPERATURE,
                top_p=TOP_P,
            )
            return response.choices[0].message.content or ""
        except Exception as error:
            errors.append(f"{provider['name']}: {error}")
            continue

    raise RuntimeError("Tất cả LLM provider đều lỗi:\n  " + "\n  ".join(errors))


# =============================================================================
# SYSTEM PROMPT
# =============================================================================

SYSTEM_PROMPT = """Bạn là trợ lý trả lời câu hỏi về chính sách thương mại điện tử và hỗ trợ
khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, quy định người bán).

Quy tắc bắt buộc:
1. Chỉ sử dụng thông tin từ context được cung cấp — KHÔNG bịa đặt
2. Mỗi khẳng định phải có trích dẫn ngay sau, ví dụ: [Returns Policy, 2026]
3. Nếu context không đủ thông tin → trả lời: "Tôi không thể xác minh thông tin này từ nguồn hiện có"
4. Trả lời bằng tiếng Việt, có cấu trúc rõ ràng theo đoạn văn
5. Không suy luận hay mở rộng ngoài những gì được nêu trong context"""


# =============================================================================
# DOCUMENT REORDERING (tránh lost in the middle)
# =============================================================================

def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """
    Sắp xếp chunks để tránh "lost in the middle" effect.

    LLM nhớ tốt thông tin ở ĐẦU và CUỐI prompt, quên thông tin ở GIỮA.
    Strategy: đặt chunks quan trọng nhất ở đầu và cuối, kém quan trọng ở giữa.

    Input order (by score):  [1, 2, 3, 4, 5]
    Output order:            [1, 3, 5, 4, 2]
    (best first, worst in middle, second-best last)

    Args:
        chunks: List sorted by score descending (from retrieval)

    Returns:
        List reordered để maximize LLM attention.
    """
    if len(chunks) <= 2:
        return list(chunks)

    front = chunks[::2]        # index 0, 2, 4 -> đặt ở đầu (chunk tốt nhất ở vị trí 0)
    back = chunks[1::2]        # index 1, 3    -> đặt ở cuối, đảo ngược
    return front + back[::-1]


# =============================================================================
# CONTEXT FORMATTING
# =============================================================================

def format_context(chunks: list[dict]) -> str:
    """
    Format chunks thành context string cho prompt.
    Mỗi chunk có label source để LLM có thể cite.

    Args:
        chunks: List of {'content': str, 'metadata': dict, 'score': float}

    Returns:
        Formatted context string.
    """
    context_parts = []
    for index, chunk in enumerate(chunks, 1):
        metadata = chunk.get("metadata") or {}
        source = metadata.get("source") or f"Source {index}"
        doc_type = metadata.get("type") or "unknown"
        context_parts.append(
            f"[Document {index} | Source: {source} | Type: {doc_type}]\n"
            f"{chunk.get('content', '')}\n"
        )
    return "\n---\n".join(context_parts)


# =============================================================================
# GENERATION
# =============================================================================

def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """
    End-to-end RAG generation có citation.

    Pipeline:
        1. Retrieve relevant chunks
        2. Reorder để tránh lost in the middle
        3. Format context với source labels
        4. Build prompt (system + context + query)
        5. Call LLM
        6. Return answer + sources

    Args:
        query: Câu hỏi của user

    Returns:
        {
            'answer': str,           # Câu trả lời có citation
            'sources': list[dict],   # Các chunks đã dùng
            'retrieval_source': str  # 'hybrid' hoặc 'pageindex'
        }
    """
    # Step 1: Retrieve (hybrid + fallback đã xử lý trong Task 9)
    chunks = retrieve(query, top_k=top_k)

    if not chunks:
        return {
            "answer": "Tôi không thể xác minh thông tin này từ nguồn hiện có.",
            "sources": [],
            "retrieval_source": "none",
        }

    # Step 2: Reorder để tránh lost in the middle
    reordered = reorder_for_llm(chunks)

    # Step 3: Format context kèm nhãn source để LLM trích dẫn được
    context = format_context(reordered)

    # Step 4: Build prompt
    user_message = f"Context:\n{context}\n\n---\n\nQuestion: {query}"

    # Step 5: Gọi LLM (tự lùi provider nếu hết quota)
    answer = _call_llm(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]
    )

    # Step 6: Trả về câu trả lời + chunks theo đúng thứ tự điểm số (không phải
    # thứ tự đã đảo cho LLM) để UI hiển thị nguồn hợp lý.
    return {
        "answer": answer,
        "sources": chunks,
        "retrieval_source": chunks[0].get("source", "hybrid"),
    }


if __name__ == "__main__":
    test_queries = [
        "Shopee hỗ trợ những phương thức thanh toán nào?",
        "Làm sao để yêu cầu đổi trả hay hoàn tiền?",
        "Cần chuẩn bị bằng chứng gì khi yêu cầu hoàn tiền?",
    ]

    for q in test_queries:
        print(f"\n{'='*70}")
        print(f"Q: {q}")
        print("=" * 70)
        result = generate_with_citation(q)
        print(f"\nA: {result['answer']}")
        print(f"\n[Sources: {len(result['sources'])} chunks | via {result['retrieval_source']}]")
