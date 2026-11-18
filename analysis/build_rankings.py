#!/usr/bin/env python3
"""Rebuild the Round 1 pressure rankings from the private organiser ZIP.

The organiser pack is intentionally not included in this repository.
Run: python analysis/build_rankings.py --zip data/private/organizer_data_pack.zip
"""
from __future__ import annotations
import argparse, json, re, zipfile
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ZIP = ROOT / "data" / "private" / "organizer_data_pack.zip"
OUT = ROOT / "app" / "data"
YEARS = set(range(2022, 2027))
MIN_PRESSURE_BALLS_BAT = 150
MIN_PRESSURE_BALLS_BOWL = 150
MIN_PRESSURE_MATCHES = 8
MIN_PRESSURE_SEASONS = 3
MIN_BASELINE_BALLS_BAT = 100
MIN_BASELINE_BALLS_BOWL = 100


def read_csv_from_zip(zf: zipfile.ZipFile, basename: str) -> pd.DataFrame:
    candidates = [n for n in zf.namelist() if n.replace("\\", "/").endswith("/" + basename)]
    if not candidates:
        raise FileNotFoundError(f"{basename} was not found inside the organiser ZIP")
    with zf.open(candidates[0]) as f:
        return pd.read_csv(f)


def zscore(series: pd.Series) -> pd.Series:
    """Winsorised cohort z-score; extreme 5% tails are clipped before scaling."""
    x = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan)
    lo, hi = x.quantile(.05), x.quantile(.95)
    x = x.clip(lo, hi)
    sd = x.std(ddof=0)
    return (x - x.mean()) / (sd if sd and np.isfinite(sd) else 1.0)


def build_pressure_deliveries(deliveries: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    d = deliveries[deliveries.innings.isin([1, 2])].copy()
    for col in ["runs", "extras1_runs", "extras_2_runs"]:
        d[col] = pd.to_numeric(d[col], errors="coerce").fillna(0)
    d["is_wicket"] = d.is_wicket.fillna(False).astype(bool)
    extras = d.extras_type.fillna("").astype(str).str.strip().str.lower()
    d["wide"] = extras.eq("wide")
    d["no_ball"] = extras.isin(["overstep", "no ball", "noball"])
    d["legal"] = ~(d.wide | d.no_ball)
    d["team_runs"] = d.runs + d.extras1_runs + d.extras_2_runs
    non_bowler_extras = extras.isin(["byes", "legbyes", "leg-byes", "penalty"])
    d["bowler_runs"] = d.runs + np.where(non_bowler_extras, 0, d.extras1_runs + d.extras_2_runs)

    d = d.sort_values(["match_id", "innings", "innings_ball_num", "overid", "over_ball_num"], kind="stable").reset_index(drop=True)
    g = d.groupby(["match_id", "innings"], sort=False)
    d["score_before"] = g.team_runs.cumsum() - d.team_runs
    d["wickets_before"] = g.is_wicket.cumsum() - d.is_wicket.astype(int)
    d["legal_balls_before"] = g.legal.cumsum() - d.legal.astype(int)
    d["current_rr"] = np.where(d.legal_balls_before > 0, d.score_before / (d.legal_balls_before / 6), 0)

    d["scheduled_overs"] = np.where(d.innings.eq(1), d.first_inn_revised_overs, d.second_inn_revised_overs)
    d["scheduled_overs"] = pd.to_numeric(d.scheduled_overs, errors="coerce").fillna(20).clip(lower=1, upper=20)
    d["balls_remaining"] = ((d.scheduled_overs * 6).round().astype(int) - d.legal_balls_before).clip(lower=0)
    first_total = d[d.innings.eq(1)].groupby("match_id").team_runs.sum()
    d["first_innings_total"] = d.match_id.map(first_total)
    d["target"] = d.first_innings_total + 1
    revised = pd.to_numeric(d.revised_target, errors="coerce")
    d.loc[revised.notna() & revised.gt(0), "target"] = revised[revised.notna() & revised.gt(0)]
    d["runs_needed"] = d.target - d.score_before
    d["required_rate"] = np.where(
        d.innings.eq(2) & d.balls_remaining.gt(0),
        d.runs_needed / (d.balls_remaining / 6), np.nan
    )

    # Pressure is measured before the delivery, using innings-specific match state.
    first_a = d.innings.eq(1) & (d.balls_remaining <= 30) & (d.wickets_before >= 4)
    first_b = d.innings.eq(1) & (d.balls_remaining <= 18) & (d.current_rr < 8.0)
    first_c = d.innings.eq(1) & (d.balls_remaining <= 12) & (d.wickets_before >= 2)
    chase_a = d.innings.eq(2) & (d.balls_remaining <= 60) & (d.required_rate >= 9.0) & (d.runs_needed > 0)
    chase_b = d.innings.eq(2) & (d.balls_remaining <= 90) & (d.required_rate >= 8.0) & (d.wickets_before >= 5) & (d.runs_needed > 0)
    chase_c = d.innings.eq(2) & (d.balls_remaining <= 30) & (d.required_rate >= 7.5) & (d.runs_needed > 0)
    d["pressure"] = first_a | first_b | first_c | chase_a | chase_b | chase_c
    d["pressure_reason"] = np.select(
        [first_a | first_b | first_c, chase_a, chase_b | chase_c],
        ["First-innings late/wicket/run-rate stress", "Chase: RRR >= 9 in final 10 overs", "Chase: high RRR with wickets down or in final 5 overs"],
        default="Normal"
    )
    return d


def aggregate_bat(d: pd.DataFrame, pressure: bool, suffix: str) -> pd.DataFrame:
    x = d[d.pressure.eq(pressure) & d.striker_id.notna() & d.batter_ball.eq(1)]
    q = x.groupby(["striker_id", "striker_name"], dropna=False).agg(
        runs=("runs", "sum"), balls=("batter_ball", "sum"), outs=("batter_out", "sum"),
        boundaries=("boundary", "sum"), matches=("match_id", "nunique"), seasons=("season", "nunique")
    )
    q["sr"] = 100 * q.runs / q.balls.replace(0, np.nan)
    # Small continuity correction prevents one/two-dismissal averages from exploding.
    q["avg"] = (q.runs + 20) / (q.outs + 1)
    q["boundary_pct"] = 100 * q.boundaries / q.balls.replace(0, np.nan)
    return q.add_suffix("_" + suffix)


def aggregate_bowl(d: pd.DataFrame, pressure: bool, suffix: str) -> pd.DataFrame:
    x = d[d.pressure.eq(pressure) & d.bowler_id.notna() & d.legal]
    q = x.groupby(["bowler_id", "bowler_name"], dropna=False).agg(
        conceded=("bowler_runs", "sum"), balls=("legal", "sum"), wickets=("bowler_wicket", "sum"),
        dots=("bowler_dot", "sum"), matches=("match_id", "nunique"), seasons=("season", "nunique")
    )
    q["economy"] = 6 * q.conceded / q.balls.replace(0, np.nan)
    q["wickets_per24"] = 24 * q.wickets / q.balls.replace(0, np.nan)
    q["dot_pct"] = 100 * q.dots / q.balls.replace(0, np.nan)
    return q.add_suffix("_" + suffix)


def add_examples(top: pd.DataFrame, d: pd.DataFrame, match_scope: pd.DataFrame, kind: str) -> list:
    meta = match_scope.set_index("match_id")
    out = []
    if kind == "batter":
        x = d[d.pressure & d.batter_ball.eq(1)].groupby(["striker_id", "striker_name", "match_id"]).agg(
            runs=("runs", "sum"), balls=("batter_ball", "sum"), team_id=("batting_team_id", "first")
        ).reset_index()
        for _, p in top.iterrows():
            cand = x[x.striker_id.eq(p.striker_id)].sort_values(["runs", "balls"], ascending=False).head(1)
            if cand.empty:
                out.append(None); continue
            q = cand.iloc[0]; m = meta.loc[q.match_id]
            opponent = m.away_team if int(q.team_id) == int(m.home_team_id) else m.home_team
            out.append({"match_date": str(m.match_date), "competition": str(m.comp_name), "opponent": str(opponent),
                        "pressure_runs": int(q.runs), "pressure_balls": int(q.balls), "match_result": str(m.result)})
    else:
        x = d[d.pressure & d.legal].groupby(["bowler_id", "bowler_name", "match_id"]).agg(
            conceded=("bowler_runs", "sum"), balls=("legal", "sum"), wickets=("bowler_wicket", "sum"), team_id=("bowling_team_id", "first")
        ).reset_index()
        for _, p in top.iterrows():
            cand = x[x.bowler_id.eq(p.bowler_id)].sort_values(["wickets", "conceded"], ascending=[False, True]).head(1)
            if cand.empty:
                out.append(None); continue
            q = cand.iloc[0]; m = meta.loc[q.match_id]
            opponent = m.away_team if int(q.team_id) == int(m.home_team_id) else m.home_team
            out.append({"match_date": str(m.match_date), "competition": str(m.comp_name), "opponent": str(opponent),
                        "pressure_wickets": int(q.wickets), "pressure_runs_conceded": int(q.conceded),
                        "pressure_legal_balls": int(q.balls), "match_result": str(m.result)})
    return out


def json_records(frame: pd.DataFrame) -> list:
    return json.loads(frame.replace({np.nan: None}).to_json(orient="records"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", type=Path, default=DEFAULT_ZIP)
    args = parser.parse_args()
    if not args.zip.exists():
        raise SystemExit(f"Data pack not found: {args.zip}\nPlace the private organiser ZIP at data/private/organizer_data_pack.zip")

    with zipfile.ZipFile(args.zip) as zf:
        competitions = read_csv_from_zip(zf, "competitions.csv")
        matches = read_csv_from_zip(zf, "matches.csv")
        deliveries = read_csv_from_zip(zf, "ball_by_ball.csv")
        mapping = read_csv_from_zip(zf, "competition_team_player_mapping.csv")
        teams = read_csv_from_zip(zf, "teams.csv")
        playing_xi = read_csv_from_zip(zf, "playing_eleven.csv")
    raw_delivery_count = len(deliveries)

    competitions["season_start"] = pd.to_numeric(competitions.season.astype(str).str.extract(r"(20\d{2})")[0], errors="coerce")
    is_ipl = competitions.comp_name.astype(str).str.match(r"^IPL\s+20\d{2}$", case=False, na=False)
    is_t20i = competitions.match_format.astype(str).str.upper().eq("T20I")
    scoped = competitions[(is_ipl | is_t20i) & competitions.season_start.isin(YEARS)].copy()
    match_scope = matches.merge(scoped[["comp_id", "comp_name", "match_format", "season"]], on="comp_id", how="inner").drop_duplicates("match_id")
    deliveries = deliveries.merge(match_scope[["match_id", "comp_name", "match_format", "season", "match_date", "home_team_id", "home_team", "away_team_id", "away_team", "result", "first_inn_revised_overs", "second_inn_revised_overs", "revised_target"]], on="match_id", how="inner")
    d = build_pressure_deliveries(deliveries, match_scope)
    d["analysis_format"] = np.where(d.comp_name.astype(str).str.match(r"^IPL\s+20\d{2}$", case=False, na=False), "IPL", "T20I")
    d["batter_ball"] = (~d.wide).astype(int)
    d["batter_out"] = (d.is_wicket & d.dismissed_player_id.notna() & (d.dismissed_player_id == d.striker_id) &
                        ~d.dismissal_type.fillna("").astype(str).str.strip().str.lower().isin(["retired hurt", "obstructing the field", "obstracting the field"]))
    d["boundary"] = d.is_four.fillna(False).astype(bool) | d.is_six.fillna(False).astype(bool)
    credited = {"caught", "bowled", "lbw", "stump", "stumped", "hit wicket", "caught and bowled"}
    d["bowler_wicket"] = (d.is_wicket & d.dismissal_type.fillna("").astype(str).str.strip().str.lower().isin(credited)).astype(int)
    d["bowler_dot"] = ((d.team_runs == 0) & d.legal).astype(int)

    # Exclusion is user-requested. The pack has no nationality column, so T20I national-team mapping is used as a transparent proxy.
    map_comp = mapping.merge(competitions[["comp_id", "match_format"]], on="comp_id", how="left")
    excluded_rows = map_comp[(map_comp.match_format.astype(str).str.upper().eq("T20I")) &
                             map_comp.team_name.astype(str).str.strip().isin(["Pakistan", "Bangladesh"])]
    excluded_ids = set(excluded_rows.player_id.dropna().astype(int))

    bat = aggregate_bat(d, True, "p").join(aggregate_bat(d, False, "n"), how="inner")
    innings = d[d.pressure & d.batter_ball.eq(1)].groupby(["striker_id", "striker_name", "match_id"]).agg(
        balls=("batter_ball", "sum"), runs=("runs", "sum")
    )
    innings = innings[innings.balls >= 6].copy()
    innings["good"] = (100 * innings.runs / innings.balls) >= 120
    bat_consistency = innings.groupby(level=[0, 1]).agg(consistency=("good", "mean"), qualifying_matches=("good", "size"))
    bat = bat.join(bat_consistency, how="left").fillna({"consistency": 0, "qualifying_matches": 0})
    bat_role = d[d.pressure & d.batter_ball.eq(1)].groupby(["striker_id", "striker_name"]).agg(
        top7_share=("batting_order", lambda s: (pd.to_numeric(s, errors="coerce") <= 7).mean())
    )
    bat = bat.join(bat_role, how="left").fillna({"top7_share": 0})
    bat["sr_uplift"] = bat.sr_p - bat.sr_n
    bat["delta_sr"] = bat.sr_uplift
    bat["avg_uplift_pct"] = 100 * (bat.avg_p - bat.avg_n) / bat.avg_n.replace(0, np.nan)
    bat["avg_uplift_pct"] = bat.avg_uplift_pct.replace([np.inf, -np.inf], np.nan).fillna(0)
    bat["boundary_uplift"] = bat.boundary_pct_p - bat.boundary_pct_n
    bat["format_mix"] = bat.index.get_level_values(0).map(
        d.groupby("striker_id").analysis_format.apply(lambda s: ", ".join(sorted(set(s))))
    )
    bat = bat[(~bat.index.get_level_values(0).astype(int).isin(excluded_ids)) &
              (bat.balls_p >= MIN_PRESSURE_BALLS_BAT) & (bat.matches_p >= MIN_PRESSURE_MATCHES) &
              (bat.seasons_p >= MIN_PRESSURE_SEASONS) & (bat.balls_n >= MIN_BASELINE_BALLS_BAT) &
              (bat.top7_share >= .50)].copy()
    for c in ["sr_p", "sr_uplift", "delta_sr", "avg_uplift_pct", "boundary_uplift", "consistency"]:
        bat["z_" + c] = zscore(bat[c])
    bat["raw_score"] = (.30 * bat.z_sr_p + .25 * bat.z_sr_uplift + .15 * bat.z_avg_uplift_pct +
                        .15 * bat.z_boundary_uplift + .15 * bat.z_consistency)
    bat["reliability"] = (np.sqrt(bat.balls_p / (bat.balls_p + 100)) *
                          np.sqrt(bat.matches_p / (bat.matches_p + 8)) *
                          np.sqrt(bat.seasons_p / (bat.seasons_p + 2)))
    bat["adjusted_score"] = 50 + 10 * bat.raw_score * bat.reliability
    bat = bat.sort_values(["adjusted_score", "balls_p"], ascending=False).copy()
    bat.insert(0, "rank", np.arange(1, len(bat) + 1))
    bat["score"] = bat.adjusted_score.rank(pct=True, method="average") * 100

    bowl = aggregate_bowl(d, True, "p").join(aggregate_bowl(d, False, "n"), how="inner")
    spells = d[d.pressure].groupby(["bowler_id", "bowler_name", "match_id"]).agg(
        balls=("legal", "sum"), conceded=("bowler_runs", "sum"), wickets=("bowler_wicket", "sum")
    )
    spells = spells[spells.balls >= 6].copy()
    spells["spell_economy"] = 6 * spells.conceded / spells.balls
    spells["good"] = (spells.spell_economy <= 8) | (spells.wickets >= 1)
    bowl_consistency = spells.groupby(level=[0, 1]).agg(consistency=("good", "mean"), qualifying_matches=("good", "size"))
    bowl = bowl.join(bowl_consistency, how="left").fillna({"consistency": 0, "qualifying_matches": 0})
    bowl["econ_improve"] = bowl.economy_n - bowl.economy_p
    bowl["delta_economy"] = bowl.econ_improve
    bowl["wkt_uplift"] = bowl.wickets_per24_p - bowl.wickets_per24_n
    bowl["dot_uplift"] = bowl.dot_pct_p - bowl.dot_pct_n
    bowl["format_mix"] = bowl.index.get_level_values(0).map(
        d.groupby("bowler_id").analysis_format.apply(lambda s: ", ".join(sorted(set(s))))
    )
    bowl = bowl[(~bowl.index.get_level_values(0).astype(int).isin(excluded_ids)) &
                (bowl.balls_p >= MIN_PRESSURE_BALLS_BOWL) & (bowl.matches_p >= MIN_PRESSURE_MATCHES) &
                (bowl.seasons_p >= MIN_PRESSURE_SEASONS) & (bowl.balls_n >= MIN_BASELINE_BALLS_BOWL)].copy()
    for c in ["wickets_per24_p", "economy_p", "econ_improve", "dot_pct_p", "dot_uplift", "consistency"]:
        bowl["z_" + c] = zscore(-bowl[c] if c == "economy_p" else bowl[c])
    bowl["raw_score"] = (.28 * bowl.z_wickets_per24_p + .24 * bowl.z_economy_p + .18 * bowl.z_econ_improve +
                         .12 * bowl.z_dot_pct_p + .08 * bowl.z_dot_uplift + .10 * bowl.z_consistency)
    bowl["reliability"] = (np.sqrt(bowl.balls_p / (bowl.balls_p + 100)) *
                           np.sqrt(bowl.matches_p / (bowl.matches_p + 8)) *
                           np.sqrt(bowl.seasons_p / (bowl.seasons_p + 2)))
    bowl["adjusted_score"] = 50 + 10 * bowl.raw_score * bowl.reliability
    bowl = bowl.sort_values(["adjusted_score", "balls_p"], ascending=False).copy()
    bowl.insert(0, "rank", np.arange(1, len(bowl) + 1))
    bowl["score"] = bowl.adjusted_score.rank(pct=True, method="average") * 100

    if len(bat) < 10 or len(bowl) < 10:
        raise ValueError("Fewer than 10 eligible players after the published sample and exclusion filters")
    top_bat = bat.head(10).reset_index()
    top_bowl = bowl.head(10).reset_index()
    top_bat["evidence_match"] = add_examples(top_bat, d, match_scope, "batter")
    top_bowl["evidence_match"] = add_examples(top_bowl, d, match_scope, "bowler")

    # Public schema preserves the simple names used by the front-end.
    bat_payload = top_bat.rename(columns={"avg_p": "avg_p", "avg_n": "avg_n"})
    bowl_payload = top_bowl.rename(columns={"economy_p": "econ_p", "economy_n": "econ_n",
                                             "wickets_per24_p": "wickets_per24_p", "wickets_per24_n": "wickets_per24_n"})
    bat_fields = ["rank", "striker_id", "striker_name", "score", "adjusted_score", "runs_p", "balls_p", "outs_p", "matches_p", "seasons_p", "sr_p", "avg_p", "boundary_pct_p", "runs_n", "balls_n", "outs_n", "matches_n", "sr_n", "avg_n", "boundary_pct_n", "sr_uplift", "delta_sr", "avg_uplift_pct", "boundary_uplift", "consistency", "qualifying_matches", "top7_share", "reliability", "format_mix", "evidence_match"]
    bowl_fields = ["rank", "bowler_id", "bowler_name", "score", "adjusted_score", "conceded_p", "balls_p", "wickets_p", "matches_p", "seasons_p", "econ_p", "wickets_per24_p", "dot_pct_p", "conceded_n", "balls_n", "wickets_n", "matches_n", "econ_n", "wickets_per24_n", "dot_pct_n", "econ_improve", "delta_economy", "wkt_uplift", "dot_uplift", "consistency", "qualifying_matches", "reliability", "format_mix", "evidence_match"]
    OUT.mkdir(parents=True, exist_ok=True)
    dashboard = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "Organizer-provided IPL and T20I data pack; raw files are kept private.",
        "scope": {
            "years": [2022, 2023, 2024, 2025, 2026], "formats": ["IPL", "T20I"],
            "competition_count": int(scoped.comp_id.nunique()), "scoped_match_count": int(match_scope.match_id.nunique()),
            "match_count": int(d.match_id.nunique()), "delivery_count": int(len(d)),
            "pressure_delivery_count": int(d.pressure.sum()), "pressure_match_count": int(d.loc[d.pressure, "match_id"].nunique()),
            "ipl_match_count": int(d.loc[d.analysis_format.eq("IPL"), "match_id"].nunique()),
            "t20i_match_count": int(d.loc[d.analysis_format.eq("T20I"), "match_id"].nunique()),
            "eligible_batter_count": int(len(bat)), "eligible_bowler_count": int(len(bowl)),
            "pressure_reason_counts": {str(k): int(v) for k, v in d.loc[d.pressure, "pressure_reason"].value_counts().items()},
        },
        "pressure_definition": {
            "first_innings": ["30 or fewer legal balls remain and at least 4 wickets have fallen", "18 or fewer legal balls remain and current run rate is below 8", "12 or fewer legal balls remain and at least 2 wickets have fallen"],
            "chase": ["Required rate at least 9 with 60 or fewer balls remaining", "Required rate at least 8 with 5 or more wickets down and 90 or fewer balls remaining", "Required rate at least 7.5 with 30 or fewer balls remaining"],
            "timing": "All match-state conditions are calculated before the delivery.",
        },
        "minimum_sample": {
            "batters": "150 pressure balls, at least 8 pressure matches, at least 3 pressure seasons, at least 100 non-pressure balls, and at least 50% of pressure balls faced in batting positions 1–7.",
            "bowlers": "150 legal pressure balls, at least 8 pressure matches, at least 3 pressure seasons, and at least 100 non-pressure legal balls.",
            "country_exclusion": "Pakistan and Bangladesh national-team mapped player IDs are excluded from candidate rankings only; all match deliveries remain in the match-state calculations.",
        },
        "scoring": {
            "batters": {"pressure_strike_rate": .30, "strike_rate_uplift_vs_baseline": .25, "smoothed_average_uplift_vs_baseline": .15, "boundary_rate_uplift_vs_baseline": .15, "pressure_innings_consistency": .15},
            "bowlers": {"pressure_wickets_per_24_legal_balls": .28, "pressure_economy_lower_is_better": .24, "economy_improvement_vs_baseline": .18, "pressure_dot_ball_rate": .12, "dot_rate_uplift_vs_baseline": .08, "pressure_outing_consistency": .10},
            "reliability_adjustment": "The weighted winsorised z-score is multiplied by sqrt(pressure balls/(pressure balls+100)) * sqrt(pressure matches/(pressure matches+8)) * sqrt(pressure seasons/(pressure seasons+2)). The adjusted score is then converted to a percentile index among eligible players.",
            "consistency_definition": {"batters": "Share of pressure innings with at least 6 balls faced and strike rate >=120.", "bowlers": "Share of pressure-bowling outings with at least 6 legal balls where economy <=8 or at least one bowler-credited wicket was taken."},
        },
        "exclusions": {
            "teams": ["Pakistan", "Bangladesh"], "excluded_player_ids_count": int(len(excluded_ids)),
            "method_note": "The organiser pack has no nationality field. Exclusion uses each player's team affiliation in T20I competition mappings. It is a transparent proxy, not a complete nationality register; unrepresented players cannot be nationality-verified from this pack alone."
        },
        "rankings": {"batters": json_records(top_bat[bat_fields]), "bowlers": json_records(bowl_payload[bowl_fields])},
        "data_quality_notes": [
            "The analysis uses the formal brief's IPL and T20I scope from 2022 onward; unrelated non-IPL T20 competitions are excluded.",
            "The selected match metadata contains more matches than the delivery file supplies usable innings records for; the analysed match count reflects matches present in the ball-by-ball data.",
            "Wides do not count as batter balls faced or bowler legal balls; no-balls count as batter balls faced but not as bowler legal balls.",
            "Batting average uses a continuity correction (runs + 20)/(dismissals + 1) to moderate very small dismissal counts.",
            "Bowler wickets include only caught, bowled, LBW, stumped, hit wicket and caught-and-bowled dismissals.",
            "Percentile index is relative to the eligible cohort and must not be interpreted as a probability or a direct skill grade.",
        ],
    }
    (OUT / "dashboard.json").write_text(json.dumps(dashboard, indent=2, ensure_ascii=False), encoding="utf-8")

    def write_csv(frame: pd.DataFrame, fields: list[str], filename: str) -> None:
        out = frame[fields].drop(columns=["evidence_match"], errors="ignore").copy()
        ex = pd.DataFrame([{
            "example_date": (e or {}).get("match_date"), "example_competition": (e or {}).get("competition"),
            "example_opponent": (e or {}).get("opponent"),
            "example_pressure_balls": (e or {}).get("pressure_balls") if "striker_name" in fields else (e or {}).get("pressure_legal_balls"),
            "example_pressure_runs": (e or {}).get("pressure_runs") if "striker_name" in fields else (e or {}).get("pressure_runs_conceded"),
            "example_pressure_wickets": (e or {}).get("pressure_wickets"), "example_match_result": (e or {}).get("match_result")
        } for e in frame["evidence_match"]])
        pd.concat([out.reset_index(drop=True), ex], axis=1).to_csv(OUT / filename, index=False)
    write_csv(top_bat, bat_fields, "top10_batters.csv")
    write_csv(bowl_payload, bowl_fields, "top10_bowlers.csv")

    audit = {
        "raw_zip": args.zip.name,
        "input_rows": {"competitions": int(len(competitions)), "teams": int(len(teams)), "matches": int(len(matches)),
                       "deliveries": int(raw_delivery_count),
                       "competition_team_player_mapping": int(len(mapping)), "playing_eleven": int(len(playing_xi))},
        "selected_competitions": int(scoped.comp_id.nunique()), "selected_match_metadata": int(match_scope.match_id.nunique()),
        "analysed_matches": int(d.match_id.nunique()), "analysed_deliveries": int(len(d)),
        "pressure_deliveries": int(d.pressure.sum()), "pressure_matches": int(d.loc[d.pressure, "match_id"].nunique()),
        "eligible_batters_after_filters": int(len(bat)), "eligible_bowlers_after_filters": int(len(bowl)),
        "excluded_player_ids_count": int(len(excluded_ids)),
    }
    (OUT / "analysis_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(audit, indent=2))
    print("\nTOP 10 BATTERS")
    print(top_bat[["rank", "striker_name", "score", "runs_p", "balls_p", "matches_p", "sr_p", "avg_p"]].round(2).to_string(index=False))
    print("\nTOP 10 BOWLERS")
    print(bowl_payload[["rank", "bowler_name", "score", "wickets_p", "balls_p", "matches_p", "econ_p"]].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
