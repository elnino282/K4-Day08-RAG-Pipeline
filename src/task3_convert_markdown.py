"""
Task 3 — Convert toàn bộ file trong data/landing/ thành Markdown.

Sử dụng MarkItDown của Microsoft:
    https://github.com/microsoft/markitdown

Cài đặt:
    pip install "markitdown[pdf]"
    # Lưu ý: cần extra [pdf] để convert được file PDF. Chỉ "pip install markitdown"
    # (không có extra) sẽ báo MissingDependencyException khi convert PDF, dù JSON/DOCX
    # vẫn convert bình thường.

Hướng dẫn:
    1. Scan toàn bộ file trong data/landing/ (PDF, DOCX, JSON)
    2. Convert sang Markdown
    3. Lưu vào data/standardized/ giữ nguyên cấu trúc thư mục
"""

import json
import sys
from datetime import date
from pathlib import Path

from markitdown import MarkItDown

LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


LEGAL_METADATA = {
    "shopee-privacy-policy": {
        "title": "Chính sách Bảo mật Shopee Việt Nam",
        "customer_role": "both",
        "category": "privacy",
        "source_url": "https://help.shopee.vn/portal/4/article/77244",
        "document_version": "2026-04-06",
    },
    "shopee-returns-refunds-policy": {
        "title": "Chính sách Trả hàng và Hoàn tiền Shopee",
        "customer_role": "both",
        "category": "returns-refunds",
        "source_url": "https://help.shopee.vn/portal/4/article/77251",
        "document_version": "2026-03-11",
    },
    "shopee-product-listing-regulations": {
        "title": "Quy định về đăng bán sản phẩm trên Shopee",
        "customer_role": "seller",
        "category": "product-listing",
        "source_url": "https://help.shopee.vn/portal/4/article/77246",
        "document_version": "not-stated",
    },
}


def _yaml_value(value: str) -> str:
    """Quote một scalar để front matter luôn là YAML hợp lệ."""
    return json.dumps(str(value), ensure_ascii=False)


def _front_matter(metadata: dict) -> str:
    lines = ["---"]
    lines.extend(f"{key}: {_yaml_value(value)}" for key, value in metadata.items())
    lines.extend(["---", ""])
    return "\n".join(lines)


def convert_legal_docs():
    """Convert PDF/DOCX files trong data/landing/legal/ sang markdown."""
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    md = MarkItDown()

    for filepath in legal_dir.iterdir():
        if filepath.suffix.lower() in (".pdf", ".docx", ".doc"):
            print(f"Converting: {filepath.name}")
            result = md.convert(str(filepath))
            extracted_text = result.text_content.strip()
            if len(extracted_text) <= 200:
                raise ValueError(
                    f"Nội dung trích xuất từ {filepath.name} quá ngắn "
                    f"({len(extracted_text)} ký tự)"
                )

            metadata = {
                "title": filepath.stem,
                "customer_role": "both",
                "category": "legal",
                "source_url": "not-stated",
                "retrieved_at": date.today().isoformat(),
                "document_version": "not-stated",
                "source_file": filepath.name,
                **LEGAL_METADATA.get(filepath.stem, {}),
            }
            output_path = output_dir / f"{filepath.stem}.md"
            output_path.write_text(
                _front_matter(metadata) + extracted_text + "\n",
                encoding="utf-8",
            )
            print(f"  ✓ Saved: {output_path}")


def convert_news_articles():
    """Convert JSON crawled articles trong data/landing/news/ sang markdown."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    for filepath in news_dir.iterdir():
        if filepath.suffix.lower() == ".json":
            print(f"Converting: {filepath.name}")
            data = json.loads(filepath.read_text(encoding="utf-8"))
            content_markdown = data.get("content_markdown", "").strip()
            if len(content_markdown) <= 200:
                raise ValueError(
                    f"Nội dung trong {filepath.name} quá ngắn "
                    f"({len(content_markdown)} ký tự)"
                )

            metadata = {
                "title": data.get("title", "Unknown"),
                "customer_role": data.get("customer_role", "both"),
                "category": data.get("category", "customer-support"),
                "source_url": data.get("url", "not-stated"),
                "retrieved_at": data.get("date_crawled", "not-stated"),
                "document_version": "not-stated",
                "source_file": filepath.name,
            }
            output_path = output_dir / f"{filepath.stem}.md"
            output_path.write_text(
                _front_matter(metadata) + content_markdown + "\n",
                encoding="utf-8",
            )
            print(f"  ✓ Saved: {output_path}")


def convert_all():
    """Convert toàn bộ files."""
    print("=" * 50)
    print("Task 3: Convert to Markdown (MarkItDown)")
    print("=" * 50)

    print("\n--- Legal Documents ---")
    convert_legal_docs()

    print("\n--- News Articles ---")
    convert_news_articles()

    print("\n✓ Done! Output tại:", OUTPUT_DIR)


if __name__ == "__main__":
    convert_all()
