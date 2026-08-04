---
title: "Riot TFT Data and App Policy Reference"
game: "Teamfight Tactics"
customer_role: "developer"
category: "official-data-policy"
source_url: "https://developer.riotgames.com/docs/tft"
retrieved_at: "2026-08-04"
document_version: "2026-08-04"
source_file: "riot-tft-data-policy.pdf"
---
# Riot TFT Data and App Policy Reference

Source: https://developer.riotgames.com/docs/tft

## Purpose and Scope

This reference document defines how the Gaming Meta Guide dataset should use official Riot Games Teamfight Tactics data. It is written as a visible source document for retrieval, not as a hidden instruction. The document helps the assistant explain where champion names, item names, trait data, augment records, patch references, and static assets should come from.
The target product is a Vietnamese TFT strategy assistant that answers practical player questions such as "Jhin lên đồ nào?", "Bard dùng Shojin hay Mũ Phù Thủy?", and "Shen cầm Găng Đạo Tặc ổn không?". The policy scope is limited to educational recommendation, source attribution, and data hygiene. It does not authorize live automation, hidden-state tracking, or claims that Riot officially endorses a student project.

## Official Data Sources

Riot developer documentation and Data Dragon are the preferred sources for canonical TFT names, identifiers, and static records. Static records can include champions, items, traits, augments, tacticians, arenas, booms, and assets. These records are useful for entity matching because they provide stable item and champion names even when the meta changes.
Official data should be treated as identity evidence. For example, Riot data can confirm that an item exists and what its official name is. Official data by itself usually does not answer which item build is strongest on a champion. To answer a meta question, the system should combine static data with build guides, item mechanics, patch notes, and meta-stat summaries.

## Allowed Educational Use

The Gaming Meta Guide may provide educational advice before or after a match. It can explain why Infinity Edge fits an attack-damage carry, why Spear of Shojin helps a caster cast more often, why Last Whisper is useful into armor-heavy frontlines, or why a flexible unit might hold Thief's Gloves when components are awkward.
The assistant may compare alternatives when the retrieved context supports that comparison. For example, it can say that Bard normally wants Găng Bảo Thạch, Mũ Phù Thủy Rabadon, and Ngọn Giáo Shojin, but Trượng Hư Vô is useful when enemies stack magic resistance. This is allowed because it explains strategic tradeoffs instead of pretending there is one permanent answer.

## Risky or Disallowed Claims

The assistant should not promise guaranteed wins, guaranteed top-four finishes, or fixed win rates unless a retrieved statistics document explicitly provides those values. It should not claim access to live hidden lobby state. It should not tell the player that a single build is mandatory in every lobby, because TFT depends on patch, item components, champion star level, augments, traits, and enemy boards.
If the dataset does not contain the requested champion, the assistant should say it cannot verify the exact build from current sources. It may provide a role-based suggestion only if retrieved context identifies the champion role. Otherwise it should ask the user for more information or suggest adding a guide for that champion.

## Source Attribution Rules

Every factual answer should cite the document that supports it. Official identity or API statements should cite this Riot TFT Data and App Policy Reference. Item capacity and item-role statements should cite the TFT Item Mechanics and Vietnamese Alias Reference. Champion-specific builds should cite the matching champion build guide. Patch-sensitive claims should cite patch notes or the Patch notes and meta freshness guide.
A good answer cites the most specific source. Example: "Jhin nên lên Vô Cực Kiếm, Kiếm Tử Thần, và Diệt Khổng Lồ vì Jhin được mô tả là carry sát thương vật lý tuyến sau trong guide này [Jhin TFT carry item build guide, 2026]." A weak answer cites only this policy document for a specific Jhin build, because the policy does not itself contain the champion build.

## Example Queries

Query: "Jhin lên đồ nào?" Expected retrieval: Jhin build guide, item mechanics, and meta methodology. Expected answer: Vô Cực Kiếm, Kiếm Tử Thần, Diệt Khổng Lồ, with Cung Xanh as an armor-heavy-lobby alternative.
Query: "Có nên dùng dữ liệu Riot để làm app TFT không?" Expected retrieval: this policy reference. Expected answer: official static data can support an educational app, but the app should avoid unfair real-time automation and should clearly attribute source documents.
Query: "Build này có luôn đúng không?" Expected retrieval: this policy reference and meta methodology. Expected answer: no, TFT builds are patch-sensitive and lobby-dependent.
