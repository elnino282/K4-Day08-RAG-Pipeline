"""All user-facing copy and UI defaults live here."""

APP_TITLE = "Gaming Meta Guide"
APP_SUBTITLE = "Trợ lý chiến thuật & phân tích meta trò chơi"
APP_ICON = "⚔️"
INPUT_PLACEHOLDER = "Hỏi về tướng, đội hình, bảng ngọc, patch meta..."
NEW_CONVERSATION_LABEL = "Trận đấu mới"
LOADING_TEXT = "Đang phân tích dữ liệu chiến thuật và tổng hợp meta..."
EMPTY_TITLE = "Bạn cần tư vấn chiến thuật gì?"
EMPTY_DESCRIPTION = "Hỏi về cách lên đồ, bảng ngọc, đội hình meta và phân tích patch mới nhất."
ERROR_TITLE = "Không thể phân tích chiến thuật"
ERROR_FALLBACK = "Đã có lỗi không xác định. Vui lòng thử lại."
INVALID_RAG_RESPONSE = "RAG returned an invalid response."
SOURCE_LABEL = "Nguồn tham khảo"
MAX_TITLE_LENGTH = 42
DEFAULT_TOP_K = 5

PROMPT_CARDS = [
    {
        "icon": "⚔️",
        "category": "League of Legends",
        "title": "Lên đồ & Bảng ngọc Aatrox",
        "query": "Cách lên đồ và bảng ngọc tối ưu cho tướng Aatrox ở vị trí Đường Trên trong bản cập nhật mới nhất?",
    },
    {
        "icon": "🌊",
        "category": "Genshin Impact",
        "title": "Đội hình Neuvillette",
        "query": "Đội hình phản ứng nguyên tố tốt nhất cho nhân vật Neuvillette trong Genshin Impact bao gồm những ai?",
    },
    {
        "icon": "🏆",
        "category": "League of Legends",
        "title": "Tướng Meta Đường Giữa",
        "query": "Những tướng nào đang meta mạnh nhất ở vị trí Đường Giữa trong patch hiện tại?",
    },
    {
        "icon": "🎯",
        "category": "Genshin Impact",
        "title": "Build trang bị tối ưu",
        "query": "Bộ trang bị và vũ khí tối ưu nhất cho nhân vật Hu Tao trong Genshin Impact là gì?",
    },
]

SUGGESTIONS = [card["query"] for card in PROMPT_CARDS]

