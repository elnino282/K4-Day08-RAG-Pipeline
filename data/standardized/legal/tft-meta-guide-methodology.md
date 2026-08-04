---
title: "TFT Meta Guide Methodology and Answering Standard"
game: "Teamfight Tactics"
customer_role: "player"
category: "meta-methodology"
source_url: "https://www.metatft.com/units"
retrieved_at: "2026-08-04"
document_version: "2026-08-04"
source_file: "tft-meta-guide-methodology.pdf"
---
# TFT Meta Guide Methodology and Answering Standard

Source: https://www.metatft.com/units

## Purpose and User Intent

This methodology document explains how the Gaming Meta Guide should combine patch notes, champion build guides, item mechanics, and statistics-oriented meta sources. It is a visible reference document for retrieval and evaluation. It should help the assistant answer practical player questions without sounding like a hidden system prompt.
The target user is a Vietnamese TFT player who wants fast strategic advice. Common queries include "Jhin lên đồ nào", "Bard dùng Shojin hay Mũ Phù Thủy", "Shen có cầm Găng Đạo Tặc được không", "đồ này thay bằng gì nếu thiếu mảnh", and "build này còn hợp patch không".

## Evidence Types

Official patch notes explain balance changes and should be used for freshness-sensitive claims. Item mechanics references explain why an item type fits a role. Champion build guides provide specific item packages for named champions. Meta statistics can suggest which item combinations are performing well in recent ranked games.
These evidence types should not be mixed carelessly. A patch note can justify that a champion or item changed, but it may not provide the best build. A community or statistics guide can recommend items, but it should not be framed as official Riot policy. The answer should make this distinction clear through citation.

## Retrieval Priority

For a champion item question, retrieval should prioritize exact champion chunks first. If the query says "Jhin lên đồ nào", the Jhin guide should outrank generic item mechanics. The final answer can then use item mechanics to explain why the recommended items make sense.
For a vague query like "tướng này lên đồ nào", the assistant should ask for the champion name unless previous conversation memory contains one. If the query mentions only an item, such as "Vô Cực Kiếm dùng cho ai", retrieval should search both the alias table and champion guides containing that item.
For patch questions, retrieval should include patch notes or the freshness guide. If no current patch evidence exists, the assistant should not pretend the data is current.

## Answer Format

Recommended Vietnamese answer format: "[Champion] nên lên [item 1] + [item 2] + [item 3]. Nếu gặp [condition], có thể thay [alternative]. Lý do: [role-based explanation]." The answer should be short enough for gameplay use but still cite the source document.
Example: "Jhin nên lên Vô Cực Kiếm + Kiếm Tử Thần + Diệt Khổng Lồ. Nếu lobby nhiều tanker giáp cao, thay một slot bằng Cung Xanh. Lý do: Jhin là carry sát thương vật lý tuyến sau nên ưu tiên sát thương, chí mạng và xuyên giáp [Jhin TFT carry item build guide, 2026]."

## Patch Freshness and Uncertainty

TFT changes frequently. A recommendation should include patch context when the source includes it. If the user asks for the newest meta and the indexed dataset does not include the newest patch note, the assistant should state that it cannot verify the newest state from the current data.
Build recommendations should be treated as flexible. Available item components, augment choices, team traits, enemy resistances, champion star level, and carry assignment can change the optimal item set. Good answers should include replacement conditions instead of giving a rigid list.

## Conflict Resolution

If two retrieved guides conflict, prefer the guide with newer patch context. If patch context is equal, present both alternatives and explain the condition for each. For example, one build may be better against tanks while another is stronger against squishy boards.
If the dataset has no guide for the requested champion, the assistant should not invent a three-item build. It may provide a role-based template only if retrieved context identifies the champion role. Otherwise it should ask for a champion name, a patch, or a source document.

## Evaluation Questions

Suggested golden dataset questions include: "Jhin lên đồ nào?", "Bard nên dùng Shojin hay Mũ Phù Thủy?", "Shen cầm Găng Đạo Tặc ổn không?", "Cung Xanh dùng khi nào?", "Nếu không có Diệt Khổng Lồ thì thay gì cho Jhin?", "Tại sao build TFT phải theo patch?", and "Tướng này lên đồ nào?" These questions test exact champion retrieval, alias matching, reasoning, citation, and patch awareness.
