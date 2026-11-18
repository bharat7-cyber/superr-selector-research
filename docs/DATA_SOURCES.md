# Data sources and provenance

## Primary competition data

**Source:** SupeRR Selector Season 2 Round 1 data pack downloaded from the Unstop Brief/Case section. The organiser ZIP includes `competitions.csv`, `teams.csv`, `matches.csv`, `ball_by_ball.csv`, `competition_team_player_mapping.csv`, `playing_eleven.csv` and the Round 1 brief.

| File | Use in this project |
|---|---|
| `competitions.csv` | Identify IPL/T20I competitions and seasons from 2022 onward |
| `matches.csv` | Match date, sides, innings length, revised target and result |
| `ball_by_ball.csv` | Delivery-level batter, bowler, extras, wickets and match-state calculations |
| `teams.csv` | Team ID/name reference |
| `competition_team_player_mapping.csv` | Player identity cross-check and participant-requested Pakistan/Bangladesh exclusion proxy |
| `playing_eleven.csv` | Appearance/playing-XI reference and inventory check |
| Round 1 brief | Formal task scope and required deliverables |

The original ZIP and raw CSVs are proprietary competition materials and are not included in this public website project. They should not be uploaded to GitHub or otherwise redistributed.

## Challenge brief

- [Unstop — SupeRR Selector Season 2](https://unstop.com/hackathons/crp-superr-selector-season-2-help-shape-rajasthan-royals-ipl-2027-auction-strategy-rajasthan-royals-1792758)
- The supplied Round 1 brief calls for top-10 batter and bowler rankings based on pressure performance from IPL and T20I data from 2022 onward, with a transparent methodology.

## Participant-requested nationality exclusion

The source data has no nationality field. To apply the requested exclusion, the pipeline identifies player IDs affiliated with the national teams named Pakistan or Bangladesh in T20I mapping records and excludes those IDs from the candidate rankings. This is a proxy and does not guarantee complete nationality identification for players without those mappings. The player deliveries are retained in the match-state calculations so removing a candidate does not remove their impact on the match context.

## Data coverage

This build selects 139 IPL/T20I competitions and 853 match records. Ball-by-ball data supplies usable innings data for 837 matches, covering 367 IPL matches and 470 T20I matches. It analyses 193,988 deliveries, of which 50,618 meet the pressure definition. Two other T20 competitions in the metadata are excluded because the formal Round 1 brief specifies IPL and T20I.

The current source mapping check reports zero unmapped competition/player pairs among the selected delivery references.
