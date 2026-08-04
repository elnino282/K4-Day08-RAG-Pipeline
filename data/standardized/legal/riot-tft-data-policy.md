---
title: "Riot TFT Data and App Policy Summary"
game: "Teamfight Tactics"
customer_role: "developer"
category: "official-data-policy"
source_url: "https://developer.riotgames.com/docs/tft"
retrieved_at: "2026-08-04"
document_version: "2026-08-04"
source_file: "riot-tft-data-policy.pdf"
---
# Riot TFT Data and App Policy Summary

Source: https://developer.riotgames.com/docs/tft

Riot's Teamfight Tactics developer documentation explains how official TFT data is exposed through
APIs and Data Dragon. Data Dragon contains static TFT data such as champions, items, traits,
augments, tacticians, arenas, and assets. Static data is useful for a Gaming Meta Guide because it
gives canonical names and IDs for champions and items.

Riot also describes approved and unapproved app behavior. School projects and training tools are
acceptable examples when they help players learn. Apps should increase decision diversity, not
remove decisions or dictate one exact play every moment. Static pre-game recommendations can be
acceptable, while real-time prescriptions based on the player's current game state can violate game-
integrity rules.

For this RAG project, item-build answers should be framed as educational recommendations based on
patch notes, meta statistics, and guide context. The assistant should avoid claiming that a build is
guaranteed to win, and should mention that meta data changes after patches.
