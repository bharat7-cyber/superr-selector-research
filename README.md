# SupeRR Selector Season 2 — Round 1 Pressure Performance Lab

A responsive, static research dashboard that ranks the top 10 batters and top 10 bowlers using IPL and T20I ball-by-ball data from 2022 onward. It is designed around the Round 1 task: identify players who sustain or improve performance in difficult match states compared with their own non-pressure baseline.

## Final outputs

- `app/` — deployable dashboard with rankings, player details, comparison and a scenario-finder prototype.
- `app/data/dashboard.json` — model settings, data coverage and final ranked players.
- `app/data/top10_batters.csv` and `app/data/top10_bowlers.csv` — downloadable final lists.
- `docs/RESULTS_SUMMARY.md` — readable top-10 tables and interpretation notes.
- `docs/METHODOLOGY.md` — pressure definition, eligibility, scoring weights, reliability adjustment and limitations.
- `analysis/build_rankings.py` — reproducible pipeline for rebuilding the results from the private organiser ZIP.

## Final analysis snapshot

The pipeline selected 139 IPL/T20I competitions and 853 match records. Usable delivery data covered 837 matches (367 IPL and 470 T20I), 193,988 deliveries and 50,618 pressure deliveries across 800 matches. The eligibility filters left 68 batters and 87 bowlers before extracting each top 10. The complete results are documented in `docs/RESULTS_SUMMARY.md`.

## Participant-requested exclusion

The participant requested exclusion of Pakistan- and Bangladesh-affiliated players. The organiser data pack has no nationality column, so the pipeline uses Pakistan/Bangladesh team affiliation in T20I mapping records as a proxy, excluding 98 player IDs from the candidate pool. This is not a complete nationality registry; players without such a T20I mapping cannot be fully nationality-verified from this dataset. Their deliveries remain in the match-state calculations, and only their eligibility as ranking candidates is excluded.

## Important interpretation

The percentile score is relative to the eligible cohort, not a probability or an absolute player-quality grade. Pressure thresholds, sample cut-offs and score weights are researcher-defined choices, not official Rajasthan Royals ratings. The task's supplied data is historical. It does not establish current player activity, fitness, availability, auction registration or franchise eligibility. Dinesh Karthik appears in the batter list because the Round 1 historical performance task does not state an active-player requirement. Do not present these rankings as an auction-availability list.

## Run the website locally (Windows)

1. Extract the project ZIP.
2. Open the `superr-selector-research` folder.
3. Double-click `START_HERE.bat`.
4. If the browser does not open automatically, visit `http://localhost:8000`.
5. Keep the terminal window open while using the site; press `Ctrl+C` to stop the local server.

You can also run `python -m http.server 8000 --directory app` from the project folder.

## Deploy to GitHub Pages

1. Create a new GitHub repository.
2. Upload the **contents** of the `superr-selector-research` folder to the repository root (not the parent ZIP wrapper).
3. Do not upload the organiser ZIP or any raw organiser CSVs. The source folder is ignored by Git.
4. In GitHub, open **Settings → Pages** and set the deployment source to **GitHub Actions**.
5. The included workflow deploys the static `app/` directory.
6. Your site URL will be `https://YOUR-USERNAME.github.io/REPOSITORY-NAME/`.

## Rebuild rankings from the private source pack

1. Download the data pack from Unstop's Brief/Case area.
2. Place it at `data/private/organizer_data_pack.zip`.
3. Install packages with `python -m pip install -r requirements.txt`.
4. Run `python analysis/build_rankings.py`.
5. Inspect `app/data/analysis_audit.json` and both CSV exports before publishing.

The organiser pack is competition-use data and is deliberately not included in this project ZIP.

## Scenario finder status

The scenario finder is a prototype that re-weights aggregate metrics from the displayed top-10 tables. It is not a separately trained model and does not yet use phase-specific ball-by-ball splits, venue, pitch, opponent matchups, injuries or player availability. Its output is a shortlist for human review, not a prediction.

## Competition integrity

Use the website to reproduce and inspect the analysis. Read the methodology and verify the selected players and examples yourself so you can explain the model and your final interpretation to the judges.
