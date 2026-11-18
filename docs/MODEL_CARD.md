# Model card

## Purpose
Rank batter and bowler performances in defined high-pressure T20 match situations using the organiser's IPL and T20I data from 2022 onward.

## Intended use
Support the SupeRR Selector Season 2 Round 1 analysis and provide a transparent, reproducible basis for comparing players within the eligible sample.

## Not intended for
- Predicting match outcomes or future individual performance.
- Claiming a player is currently active, fit, available, auction-registered or eligible for a franchise.
- Comparing batter and bowler scores as if they measure the same skill.
- Replacing scouting, tactical review or human judgement.

## Inputs and output
The pipeline uses organiser competition, match and delivery records, with team/player mapping and playing-XI tables as reference material. It produces a top-10 batter list and a top-10 bowler list, with pressure metrics, baseline metrics and one illustrative match example per player where available.

## Eligibility and scoring
Players need at least 150 pressure balls, 8 pressure matches, 3 pressure seasons and 100 non-pressure baseline balls. Batters additionally need at least half their pressure balls in positions 1–7. A reliability adjustment reduces the impact of players closer to the minimum sample. The weights and details are in `METHODOLOGY.md`.

## Requested country exclusion and limitation
Pakistan- and Bangladesh-affiliated player IDs are excluded using T20I team mapping as a proxy because the source pack has no nationality field. This cannot fully verify nationality for players without those mapping records.

## Known risks
Pressure definitions, thresholds and weights are analyst choices. IPL and T20I are pooled even though their conditions differ. Minimum sample rules reduce but do not eliminate sample noise. Mapping gaps, shortened innings, revised targets and data-entry issues can affect eligibility and pressure-state calculations. The percentile score is relative to this eligible cohort and is not a probability or an absolute rating.

## Human review required
The participant should inspect the result tables, confirm the pressure definition, understand the metrics and weights, and personally verify the rankings and match examples before submission.
