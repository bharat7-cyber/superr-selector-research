# Methodology — SupeRR Selector Season 2 Round 1

## Objective and scope
The supplied Round 1 brief asks for the top 10 batters and top 10 bowlers whose performance is strongest and most consistent under pressure, using IPL and T20I ball-by-ball data from 2022 onward. This analysis pools IPL and T20I observations; it does not infer auction registration, active status or franchise eligibility.

## Source data and coverage
The organiser ZIP is processed locally and is not redistributed. The analysis selects 139 IPL/T20I competitions and 853 match records. Usable ball-by-ball data covers 837 matches (367 IPL and 470 T20I), 193,988 deliveries and 50,618 pressure deliveries across 800 matches. The candidate pool after all filters contains 68 batters and 87 bowlers.

## Pressure states
All match states are calculated immediately before each delivery.

**First innings — a delivery is pressure if any condition applies:**
- 30 or fewer legal balls remain and at least 4 wickets have fallen; or
- 18 or fewer legal balls remain and the current run rate is below 8; or
- 12 or fewer legal balls remain and at least 2 wickets have fallen.

**Chase — a delivery is pressure if any condition applies and the target has not been reached:**
- required rate is at least 9 with 60 or fewer legal balls remaining; or
- required rate is at least 8, at least 5 wickets have fallen, and 90 or fewer legal balls remain; or
- required rate is at least 7.5 with 30 or fewer legal balls remaining.

## Eligibility
Both roles need at least 150 pressure balls (batter balls faced or bowler legal balls), 8 pressure matches, 3 pressure seasons and 100 non-pressure baseline balls. Batters also need at least 50% of pressure balls faced in positions 1–7. These cut-offs are analyst choices designed to reduce small-sample rankings; they are not specified by the organiser.

## Country exclusion requested by participant
The participant requested that Pakistani and Bangladeshi players be excluded. The pack does not include a nationality field. The pipeline therefore excludes player IDs whose team affiliation is Pakistan or Bangladesh in T20I competition mappings. This is a transparent proxy, not a complete nationality register. IDs without such T20I mappings cannot be fully nationality-verified from this pack. The excluded candidates are removed only from the ranking pool; their match deliveries remain in match-state calculations.

## Scoring
Metrics are winsorised at the 5th and 95th percentiles and converted to cohort z-scores before applying the weights. The weighted score is multiplied by a reliability factor: `sqrt(pressure balls / (pressure balls + 100)) × sqrt(pressure matches / (pressure matches + 8)) × sqrt(pressure seasons / (pressure seasons + 2))`. The adjusted score is converted to a 0–100 percentile index within the eligible cohort. It is not a probability or universal player rating.

**Batters:** pressure strike rate 30%; strike-rate uplift over personal baseline 25%; smoothed-average uplift 15%; boundary-rate uplift 15%; pressure-innings consistency 15%. Smoothed average is `(pressure runs + 20) / (pressure dismissals + 1)`. Consistency is the share of pressure innings with at least 6 balls faced and strike rate of at least 120.

**Bowlers:** wickets per 24 pressure legal balls 28%; lower pressure economy 24%; economy improvement over personal baseline 18%; pressure dot-ball rate 12%; dot-rate uplift 8%; pressure-outing consistency 10%. Consistency is the share of bowler-match pressure outings with at least 6 legal balls where economy is at most 8 or at least one bowler-credited wicket is taken.

## Delivery accounting
Wides are not batter balls faced or bowler legal balls. No-balls count as balls faced but are not legal deliveries. Bowler runs conceded exclude byes, leg-byes and penalty runs. Bowler wickets include caught, bowled, LBW, stumped, hit wicket and caught-and-bowled.

## Limitations
IPL and T20I are pooled even though opposition strength and match environments differ. The pressure rules and weights are researcher-defined, not official Rajasthan Royals ratings. Historical results do not establish current fitness, availability, active status, auction registration or future performance. Data availability and mapping quality can affect player eligibility. Results should be interpreted with match evidence and the full ranking audit, not as proof that one player is universally better than another.
