---
title: "How to answer TFT item build questions"
game: "Teamfight Tactics"
customer_role: "player"
category: "qa-pattern"
champion: "generic"
patch_context: "General TFT guide pattern"
source_url: "https://tftguide.org/en"
retrieved_at: "2026-08-04"
document_version: "not-stated"
source_file: "article_04.json"
---
# How to answer TFT item build questions

For the query "tướng này lên đồ nào", the assistant should first identify the champion. If no
champion is named, ask the user to provide one. If the champion is named, answer with three parts:
best core items, replacement items, and short reasoning.

The response should be concise and practical. Use Vietnamese item names if the user asks in
Vietnamese, and include English aliases in parentheses when helpful. Mention that TFT item builds
depend on patch, lobby, available components, and whether the unit is used as a carry, tank, utility
holder, or temporary item holder.

Example answer structure: [Champion] nên lên [core item 1] + [core item 2] + [core item 3]. Có thể
thay [alternative] khi [condition]. Lý do: [role-based explanation].
