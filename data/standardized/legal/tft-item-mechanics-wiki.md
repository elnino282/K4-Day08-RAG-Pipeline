---
title: "TFT Item Mechanics and Vietnamese Alias Reference"
game: "Teamfight Tactics"
customer_role: "player"
category: "item-mechanics"
source_url: "https://wiki.leagueoflegends.com/en-us/TFT:Item"
retrieved_at: "2026-08-04"
document_version: "2026-08-04"
source_file: "tft-item-mechanics-wiki.pdf"
---
# TFT Item Mechanics and Vietnamese Alias Reference

Source: https://wiki.leagueoflegends.com/en-us/TFT:Item

## Purpose and Scope

This reference document describes TFT item behavior and the Vietnamese item aliases used by the Gaming Meta Guide. It is designed for retrieval when Vietnamese players ask item-build questions. The same item can appear in English in meta websites and in Vietnamese in user questions, so the dataset stores both forms.
The document does not try to replace the official game client. Instead, it creates a practical translation and reasoning layer for RAG. When the assistant sees "Vô Cực Kiếm", it should also be able to match "Infinity Edge". When it sees "Shojin", it should connect the query to "Spear of Shojin" and "Ngọn Giáo Shojin".

## Core Item Rules

A TFT champion can hold up to three completed items. If a champion is sold, equipped items return to the player. If champion copies combine and the resulting unit would exceed the item limit, excess items are dropped back to the bench or item inventory. A build recommendation should therefore describe a three-item core but still allow partial item states.
Item effects vary by item. Some provide raw damage, some provide durability, some increase casting frequency, and some solve a specific defensive problem such as armor or magic resistance. A guide should not blindly stack one stat without explaining why the champion wants it.

## Role-Based Item Logic

Attack-damage carries usually value attack damage, critical strike, attack speed, armor reduction, and damage multipliers. Vô Cực Kiếm, Kiếm Tử Thần, Diệt Khổng Lồ, and Cung Xanh are typical examples in this dataset. These items fit a backline physical carry such as Jhin because the unit wants to remove targets with high-damage attacks.
Magic-damage carries usually value ability power, spell critical strike, mana generation, magic penetration, and damage multipliers. Găng Bảo Thạch, Mũ Phù Thủy Rabadon, Ngọn Giáo Shojin, Trượng Hư Vô, and Diệt Khổng Lồ are typical examples. These items fit a caster such as Bard because they increase cast damage or cast frequency.
Frontline tanks and bruisers usually value health, armor, magic resistance, shields, healing, and sustain. Huyết Kiếm and Bàn Tay Công Lý can fit bruisers that deal damage while surviving. Găng Đạo Tặc can be a flexible choice when the unit is not the main carry or when the player has awkward item components.

## Vietnamese Item Alias Table

Infinity Edge = Vô Cực Kiếm. Deathblade = Kiếm Tử Thần. Giant Slayer = Diệt Khổng Lồ. Last Whisper = Cung Xanh. Thief's Gloves = Găng Đạo Tặc. Bloodthirster = Huyết Kiếm. Hand of Justice = Bàn Tay Công Lý. Guinsoo's Rageblade = Cuồng Đao Guinsoo. Jeweled Gauntlet = Găng Bảo Thạch. Rabadon's Deathcap = Mũ Phù Thủy Rabadon. Spear of Shojin = Ngọn Giáo Shojin. Void Staff = Trượng Hư Vô.
The assistant should accept either language. If the user asks in Vietnamese, answer primarily in Vietnamese and include English names in parentheses only when useful. If the user asks using English item names, the answer can still mention Vietnamese aliases for clarity.

## Champion Examples

Jhin example: Vô Cực Kiếm + Kiếm Tử Thần + Diệt Khổng Lồ is an attack-damage carry package. Cung Xanh is a replacement when enemy frontlines have high armor. This answer should cite the Jhin guide for the champion-specific build and this mechanics reference for role-based explanation.
Bard example: Găng Bảo Thạch + Mũ Phù Thủy Rabadon + Ngọn Giáo Shojin is a magic-carry package. Trượng Hư Vô is a replacement when enemies build magic resistance, and Diệt Khổng Lồ is useful into high-health boards.
Shen example: Găng Đạo Tặc is a flexible holder option. Huyết Kiếm + Bàn Tay Công Lý + Cuồng Đao Guinsoo can be used when Shen is expected to fight for a long time and benefit from sustain plus repeated attacks.

## Common User Questions

Question: "Jhin lên Vô Cực Kiếm được không?" Answer direction: yes, Vô Cực Kiếm is part of the Jhin core in this dataset, usually paired with Kiếm Tử Thần and Diệt Khổng Lồ.
Question: "Bard nên lên Shojin hay Mũ Phù Thủy?" Answer direction: both can be core. Ngọn Giáo Shojin helps Bard cast more often, while Mũ Phù Thủy Rabadon increases spell damage.
Question: "Shen cầm Găng Đạo Tặc có phí không?" Answer direction: it can be useful when components are awkward or Shen is a flexible holder, but exact value depends on composition and lobby.
