---
title: "TFT champion item recommendation data"
game: "Teamfight Tactics"
customer_role: "player"
category: "champion-item-matrix"
patch_context: "Set 17 item recommendation examples plus role-based fallback rules"
source_url: "https://www.metatft.com/units; https://op.gg/tft/meta-trends/champion; https://raw.communitydragon.org/latest/cdragon/tft/en_us.json"
retrieved_at: "2026-08-04"
document_version: "not-stated"
source_file: "article_02.json"
---
# TFT champion item recommendation data

This document is the item-recommendation data layer for the RAG assistant. It is not application logic. Champion-specific rows are meta examples from public TFT guide/stat sites; role-based rows are fallback guidance so the assistant can answer cautiously when the exact champion is present in the roster data but not in the champion-specific build table.

## Champion-specific item rows

| Champion | Core items | Tên Việt | Alternatives | Why |
|---|---|---|---|---|
| Aatrox | Gargoyle Stoneplate, Bramble Vest, Dragon's Claw | Thú Tượng Thạch Giáp, Giáp Gai, Vuốt Rồng | Steadfast Heart, Sterak's Gage, Warmog's Armor, Spirit Visage | Aatrox is a frontline bruiser/tank, so durability and sustain help him survive while dealing physical damage. |
| Jhin | Infinity Edge, Deathblade, Giant Slayer | Vô Cực Kiếm, Kiếm Tử Thần, Diệt Khổng Lồ | Last Whisper, Red Buff, Striker's Flail | Jhin is an AD backline carry, so damage, critical scaling, and anti-tank damage are prioritized. |
| Shen | Thief's Gloves, Bloodthirster, Hand of Justice | Găng Đạo Tặc, Huyết Kiếm, Bàn Tay Công Lý | Guinsoo's Rageblade, Titan's Resolve, defensive items | Shen is a frontline utility bruiser. Flexible or sustain items are good when he must survive and keep casting. |
| Bard | Jeweled Gauntlet, Rabadon's Deathcap, Spear of Shojin | Găng Bảo Thạch, Mũ Phù Thủy Rabadon, Ngọn Giáo Shojin | Void Staff, Giant Slayer, Blue Buff | Bard is an AP caster, so spell damage and mana generation are valuable. |
| Xayah | Kraken's Fury, Red Buff, Last Whisper | Cuồng Nộ Kraken, Bùa Đỏ, Cung Xanh | Guinsoo's Rageblade, Battle Bunny Crossbow, Infinity Edge | Xayah is a ranged AD carry, so attack-speed scaling, anti-heal/burn pressure, and armor handling are prioritized. |
| Miss Fortune | Infinity Edge, Giant Slayer, Spear of Shojin | Vô Cực Kiếm, Diệt Khổng Lồ, Ngọn Giáo Shojin | Red Buff, Last Whisper, Deathblade | Miss Fortune can use carry items that amplify ranged damage and casting uptime. |
| Ornn | Gargoyle Stoneplate, Warmog's Armor, Dragon's Claw | Thú Tượng Thạch Giáp, Giáp Máu Warmog, Vuốt Rồng | Bramble Vest, Steadfast Heart, Redemption | Ornn is usually a frontline tank or utility holder, so durability is preferred. |

## Role-based fallback item rows

| Champion role from roster | Recommended item families | Vietnamese item examples | Answering caveat |
|---|---|---|---|
| ADCarry | attack speed, attack damage, critical damage, armor shred, anti-heal | Cuồng Đao Guinsoo, Vô Cực Kiếm, Kiếm Tử Thần, Cung Xanh, Bùa Đỏ, Diệt Khổng Lồ, Cuồng Nộ Kraken | Say this is role-based if there is no champion-specific meta row. |
| ADCaster | attack damage plus mana/cast uptime and anti-tank tools | Kiếm Tử Thần, Diệt Khổng Lồ, Ngọn Giáo Shojin, Cung Xanh, Bùa Đỏ | Good for physical units whose spell is important. |
| ADFighter / ADReaper | sustain, hybrid durability, attack damage, short-range survival | Huyết Kiếm, Bàn Tay Công Lý, Quyền Năng Khổng Lồ, Móng Vuốt Sterak, Áo Choàng Bóng Tối | Needs more defense than a backline carry. |
| APCarry / APCaster | ability power, mana generation, spell critical damage, magic resistance shred | Găng Bảo Thạch, Mũ Phù Thủy Rabadon, Ngọn Giáo Shojin, Bùa Xanh, Trượng Hư Vô | Best when the champion deals most damage through abilities. |
| APFighter / APReaper | AP damage plus sustain or defensive uptime | Găng Bảo Thạch, Bàn Tay Công Lý, Huyết Kiếm, Quyền Năng Khổng Lồ, Mũ Phù Thủy Rabadon | Use when the unit fights near the frontline. |
| APTank / ADTank | armor, magic resist, health, shielding, healing, damage reduction | Thú Tượng Thạch Giáp, Giáp Gai, Vuốt Rồng, Giáp Máu Warmog, Trái Tim Kiên Định, Dây Chuyền Chuộc Tội | Use for frontline units expected to absorb damage. |

## Example response patterns

- If asked "Xayah lên đồ nào", answer from the Xayah row: Cuồng Nộ Kraken + Bùa Đỏ + Cung Xanh, then mention alternatives.
- If asked about a champion that exists in the roster but has no champion-specific build row, retrieve that champion's role from the roster and answer with the role-based fallback, explicitly saying the dataset does not contain a verified top-statistical build for that exact champion.
- If asked about a champion that does not exist in the roster, say the current dataset cannot verify that champion.
