"""
Task 2 — Crawl bài viết/hướng dẫn hỗ trợ khách hàng về thương mại điện tử.

Hướng dẫn:
    1. Crawl tối thiểu 5 bài viết từ trung tâm trợ giúp công khai của một sàn TMĐT.
    2. Sử dụng Crawl4AI hoặc thư viện crawling tương tự.
    3. Lưu output vào data/landing/news/
    4. Mỗi bài lưu 1 file JSON với metadata (url, title, date_crawled, content).

Cài đặt:
    pip install crawl4ai
    playwright install chromium   # bắt buộc — pip install crawl4ai KHÔNG tự tải browser binary,
                                   # thiếu bước này sẽ báo lỗi
                                   # "BrowserType.launch: Executable doesn't exist"

Gợi ý chủ đề: theo dõi đơn hàng, đổi phương thức thanh toán, bằng chứng hoàn tiền,
mua hàng xuyên biên giới.

Lưu ý: một số trang help center dùng JavaScript render (SPA) — nếu crawl về chỉ thấy
tiêu đề mà không có nội dung, đổi sang bài viết khác cùng domain thay vì cố xử lý.
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data" / "landing" / "news"

# Crawl4AI có một số cache (bao gồm robots.txt SQLite) luôn dựa vào biến môi
# trường này, kể cả khi AsyncWebCrawler đã nhận base_directory.
os.environ["CRAWL4_AI_BASE_DIRECTORY"] = str(PROJECT_DIR)

# Rich/Crawl4AI có dùng ký hiệu Unicode trong log; tránh lỗi cp1252 trên
# Windows PowerShell cũ khi stdout không tự nhận UTF-8.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def setup_directory():
    """Tạo thư mục data/landing/news/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


ARTICLE_URLS = [
    "https://help.shopee.vn/portal/4/article/79198",
    "https://help.shopee.vn/portal/4/article/189473",
    "https://help.shopee.vn/portal/4/article/79084",
    "https://help.shopee.vn/portal/4/article/79556",
    "https://help.shopee.vn/portal/4/article/77247",
]


# Metadata K4 được giữ ngay từ landing zone để các task retrieval phía sau có thể
# lọc theo vai trò khách hàng mà không cần suy đoán lại từ nội dung.
ARTICLE_METADATA = {
    ARTICLE_URLS[0]: {
        "title": "Các phương thức thanh toán hiện có trên Shopee",
        "customer_role": "buyer",
        "category": "payment",
    },
    ARTICLE_URLS[1]: {
        "title": "Thời gian nhận tiền hoàn và cách kiểm tra tiền hoàn",
        "customer_role": "buyer",
        "category": "refund",
    },
    ARTICLE_URLS[2]: {
        "title": "Xử lý khi đơn hàng cập nhật sai trạng thái hoặc chưa nhận được hàng",
        "customer_role": "buyer",
        "category": "order-tracking",
    },
    ARTICLE_URLS[3]: {
        "title": "Thời gian giao đơn hàng Quốc tế",
        "customer_role": "buyer",
        "category": "cross-border-shipping",
    },
    ARTICLE_URLS[4]: {
        "title": "Chính sách Cấm/Hạn chế Sản phẩm",
        "customer_role": "seller",
        "category": "prohibited-products",
    },
}


def _markdown_text(markdown) -> str:
    """Chuẩn hóa output markdown giữa các phiên bản Crawl4AI."""
    if isinstance(markdown, str):
        return markdown.strip()

    for attribute in ("raw_markdown", "fit_markdown"):
        value = getattr(markdown, attribute, None)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return str(markdown or "").strip()


async def _crawl_with_browser(crawler, url: str) -> dict:
    """Crawl một URL bằng browser đã khởi động sẵn."""
    from crawl4ai import CrawlerRunConfig

    run_config = CrawlerRunConfig(
        wait_until="networkidle",
        page_timeout=90_000,
        delay_before_return_html=2.0,
        remove_overlay_elements=True,
        remove_consent_popups=True,
    )
    result = await crawler.arun(url=url, config=run_config)

    if not result.success:
        raise RuntimeError(f"Không crawl được {url}: {result.error_message}")

    content = _markdown_text(result.markdown)
    if len(content) <= 500:
        raise RuntimeError(
            f"Nội dung crawl từ {url} quá ngắn ({len(content)} ký tự); "
            "trang có thể chưa render xong"
        )

    expected = ARTICLE_METADATA.get(url, {})
    crawled_metadata = result.metadata or {}
    return {
        "url": url,
        "title": crawled_metadata.get("title") or expected.get("title", "Unknown"),
        "date_crawled": datetime.now(timezone.utc).isoformat(),
        "customer_role": expected.get("customer_role", "both"),
        "category": expected.get("category", "customer-support"),
        "content_markdown": content,
    }


async def crawl_article(url: str) -> dict:
    """
    Crawl một bài viết và trả về dict chứa metadata + content.

    Returns:
        {
            "url": str,
            "title": str,
            "date_crawled": str (ISO format),
            "content_markdown": str
        }
    """
    from crawl4ai import AsyncWebCrawler, BrowserConfig

    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True,
        verbose=False,
    )
    async with AsyncWebCrawler(
        config=browser_config,
        base_directory=str(PROJECT_DIR),
    ) as crawler:
        return await _crawl_with_browser(crawler, url)


async def crawl_all():
    """Crawl toàn bộ bài viết trong ARTICLE_URLS."""
    from crawl4ai import AsyncWebCrawler, BrowserConfig

    setup_directory()

    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True,
        verbose=False,
    )
    async with AsyncWebCrawler(
        config=browser_config,
        base_directory=str(PROJECT_DIR),
    ) as crawler:
        for i, url in enumerate(ARTICLE_URLS, 1):
            print(f"[{i}/{len(ARTICLE_URLS)}] Crawling: {url}")
            article = await _crawl_with_browser(crawler, url)

            filename = f"article_{i:02d}.json"
            filepath = DATA_DIR / filename
            filepath.write_text(
                json.dumps(article, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"  ✓ Saved: {filepath}")


if __name__ == "__main__":
    if not ARTICLE_URLS:
        print("⚠ Hãy điền ARTICLE_URLS trước khi chạy!")
        print("Gợi ý: tìm trang hướng dẫn/hỗ trợ khách hàng trên help center của sàn TMĐT")
    else:
        asyncio.run(crawl_all())
