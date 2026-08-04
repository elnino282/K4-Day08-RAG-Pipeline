"""
Task 8 — PageIndex Vectorless RAG.

Đăng ký tài khoản tại: https://pageindex.ai/
SDK & sample code: https://github.com/VectifyAI/PageIndex

PageIndex cho phép RAG mà không cần vector store — sử dụng
structural understanding của document thay vì embedding.

Cài đặt:
    pip install pageindex fpdf2

Hướng dẫn:
    1. Đăng ký account tại pageindex.ai
    2. Lấy API key
    3. Upload documents
    4. Query sử dụng PageIndex API

Lưu ý: API `/retrieval` của PageIndex hiện đã deprecated (vẫn hoạt động, nhưng response
có field "deprecation" cảnh báo) và trả kết quả trong "retrieved_nodes" — mỗi node có
"relevant_contents": list[list[{section_title, relevant_content}]]. In response thật ra
(json.dumps(...)) trước khi viết logic parse, đừng đoán schema từ ví dụ code cũ.
"""

from __future__ import annotations

import json
import os
import time
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = PROJECT_ROOT / "data" / "standardized"

# File lưu mapping {filename_stem: doc_id} để tránh upload lại mỗi lần
DOC_ID_CACHE_FILE = PROJECT_ROOT / ".pageindex_doc_ids.json"

# Timeout tối đa khi poll status xử lý document (giây)
UPLOAD_POLL_TIMEOUT = 300
RETRIEVAL_POLL_TIMEOUT = 60


# ---------------------------------------------------------------------------
# Helper: Client
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _get_client():
    """Trả về cached PageIndexClient. Raise nếu API key chưa được set."""
    from pageindex.client import PageIndexClient

    if not PAGEINDEX_API_KEY:
        raise EnvironmentError(
            "PAGEINDEX_API_KEY chưa được cấu hình. "
            "Thêm PAGEINDEX_API_KEY=... vào file .env của dự án."
        )
    return PageIndexClient(api_key=PAGEINDEX_API_KEY)


# ---------------------------------------------------------------------------
# Helper: Markdown → PDF (PageIndex chỉ nhận PDF)
# ---------------------------------------------------------------------------

def _markdown_to_pdf(md_file: Path, pdf_path: Path) -> None:
    """Chuyển đổi file Markdown sang PDF đơn giản bằng fpdf2."""
    from fpdf import FPDF

    content = md_file.read_text(encoding="utf-8")

    pdf = FPDF(format="A4")
    pdf.set_margins(left=10, top=10, right=10)
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    pdf.set_font("Helvetica", size=9)

    page_width = pdf.w - pdf.l_margin - pdf.r_margin  # ~190mm

    for line in content.splitlines():
        # Bỏ qua ký tự ngoài latin-1 (core font)
        safe_line = line.encode("latin-1", errors="replace").decode("latin-1")
        if not safe_line.strip():
            pdf.ln(3)
            continue
        try:
            pdf.multi_cell(page_width, 4, safe_line)
        except Exception:
            # Dòng quá dài — cắt thô và thử lại
            pdf.multi_cell(page_width, 4, safe_line[:200])

    pdf.output(str(pdf_path))

# ---------------------------------------------------------------------------
# Helper: Doc ID cache
# ---------------------------------------------------------------------------

def _load_doc_id_cache() -> dict[str, str]:
    """Load mapping {stem: doc_id} từ file cache."""
    if DOC_ID_CACHE_FILE.exists():
        try:
            return json.loads(DOC_ID_CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_doc_id_cache(cache: dict[str, str]) -> None:
    """Lưu mapping {stem: doc_id} ra file cache."""
    DOC_ID_CACHE_FILE.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Upload documents
# ---------------------------------------------------------------------------

def upload_documents(force: bool = False) -> dict[str, str]:
    """
    Upload toàn bộ markdown documents lên PageIndex.

    Quy trình:
        1. Convert .md → .pdf (fpdf2)
        2. Upload PDF lên PageIndex
        3. Poll cho đến khi retrieval_ready == True
        4. Lưu doc_id cache để không upload lại lần sau

    Args:
        force: Nếu True, bỏ qua cache và upload lại tất cả.

    Returns:
        dict {filename_stem: doc_id}
    """
    client = _get_client()
    cache = {} if force else _load_doc_id_cache()
    pdf_dir = PROJECT_ROOT / "_pageindex_pdfs"
    pdf_dir.mkdir(exist_ok=True)

    md_files = sorted(STANDARDIZED_DIR.rglob("*.md"))
    if not md_files:
        raise FileNotFoundError(f"Không tìm thấy file .md trong {STANDARDIZED_DIR}")

    for md_file in md_files:
        stem = md_file.stem
        if stem in cache and not force:
            print(f"  ✓ Skip (cached): {md_file.name} → doc_id={cache[stem]}")
            continue

        # Bước 1: Convert sang PDF
        pdf_path = pdf_dir / f"{stem}.pdf"
        print(f"  → Converting: {md_file.name}", flush=True)
        _markdown_to_pdf(md_file, pdf_path)

        # Bước 2: Upload
        print(f"  → Uploading: {pdf_path.name}", flush=True)
        resp = client.submit_document(str(pdf_path))
        doc_id = resp.get("doc_id") or resp.get("id")
        if not doc_id:
            print(f"  ⚠ Không lấy được doc_id cho {md_file.name}: {resp}")
            continue

        print(f"     doc_id={doc_id}, đang chờ xử lý...", flush=True)

        # Bước 3: Poll retrieval_ready
        deadline = time.time() + UPLOAD_POLL_TIMEOUT
        while time.time() < deadline:
            if client.is_retrieval_ready(doc_id):
                print(f"  ✓ Ready: {md_file.name} → doc_id={doc_id}")
                break
            time.sleep(5)
        else:
            print(f"  ⚠ Timeout: {md_file.name} vẫn chưa ready sau {UPLOAD_POLL_TIMEOUT}s")

        cache[stem] = doc_id
        _save_doc_id_cache(cache)

    return cache


# ---------------------------------------------------------------------------
# Public API: pageindex_search
# ---------------------------------------------------------------------------

def _query_single_doc(args: tuple) -> list[dict]:
    """Worker function: query một document và trả về list results.
    Dùng bởi ThreadPoolExecutor trong pageindex_search().
    """
    client, stem, doc_id, query = args
    results: list[dict] = []
    try:
        # Gửi query
        resp = client.submit_query(doc_id=doc_id, query=query)
        retrieval_id = resp.get("retrieval_id") or resp.get("id")
        if not retrieval_id:
            return results

        # Poll cho đến khi completed
        deadline = time.time() + RETRIEVAL_POLL_TIMEOUT
        retrieval = None
        while time.time() < deadline:
            retrieval = client.get_retrieval(retrieval_id)
            status = retrieval.get("status", "")
            if status in ("completed", "failed"):
                break
            time.sleep(2)

        if not retrieval or retrieval.get("status") != "completed":
            return results

        # Parse retrieved_nodes
        # Schema: {"retrieved_nodes": [{"relevant_contents": [[{"section_title", "relevant_content"}]]}]}
        rank = 1
        for node in retrieval.get("retrieved_nodes", []):
            for group in node.get("relevant_contents", []):
                for item in (group if isinstance(group, list) else [group]):
                    content = item.get("relevant_content", "").strip()
                    section = item.get("section_title", "")
                    if not content:
                        continue
                    results.append(
                        {
                            "content": content,
                            "score": round(1.0 / rank, 4),
                            "metadata": {
                                "source": stem,
                                "section": section,
                                "doc_id": doc_id,
                            },
                            "source": "pageindex",
                        }
                    )
                    rank += 1

    except Exception as exc:
        print(f"  ⚠ Lỗi khi query doc_id={doc_id}: {exc}")

    return results


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval sử dụng PageIndex.
    Dùng làm fallback khi hybrid search không có kết quả tốt.

    Quy trình:
        1. Gửi query lên toàn bộ doc_id song song (ThreadPoolExecutor)
        2. Poll cho đến khi retrieval hoàn thành
        3. Parse retrieved_nodes → relevant_contents
        4. Gán score theo rank (1.0 / rank)

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,
            'metadata': dict,
            'source': 'pageindex'   # Đánh dấu nguồn retrieval
        }
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    client = _get_client()
    cache = _load_doc_id_cache()

    if not cache:
        print("  ⚠ Chưa có doc_id nào. Hãy chạy upload_documents() trước.")
        return []

    # Tạo args cho mỗi document
    task_args = [(client, stem, doc_id, query) for stem, doc_id in cache.items()]

    all_results: list[dict] = []

    # Query tất cả documents song song — giảm thời gian từ N×T xuống ~T
    with ThreadPoolExecutor(max_workers=min(len(task_args), 8)) as executor:
        futures = {executor.submit(_query_single_doc, args): args[1] for args in task_args}
        for future in as_completed(futures):
            try:
                all_results.extend(future.result())
            except Exception as exc:
                stem = futures[future]
                print(f"  ⚠ Thread lỗi cho {stem}: {exc}")

    # Sắp xếp theo score giảm dần và trả top_k
    all_results.sort(key=lambda x: x["score"], reverse=True)
    return all_results[:top_k]


if __name__ == "__main__":
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if not PAGEINDEX_API_KEY:
        print("⚠ Hãy set PAGEINDEX_API_KEY trong file .env")
        print("  Đăng ký tại: https://pageindex.ai/")
    else:
        print("Uploading documents...")
        upload_documents()

        print("\nTest query:")
        results = pageindex_search("danh sách sản phẩm cấm đăng bán", top_k=3)
        for r in results:
            print(f"[{r['score']:.3f}] [{r['metadata'].get('section','')}] {r['content'][:100]}...")
