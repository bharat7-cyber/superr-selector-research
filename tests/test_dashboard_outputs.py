import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'app' / 'data'


def test_dashboard_has_two_ordered_top_tens():
    payload = json.loads((DATA / 'dashboard.json').read_text(encoding='utf-8'))
    bat = payload['rankings']['batters']
    bowl = payload['rankings']['bowlers']
    assert len(bat) == 10
    assert len(bowl) == 10
    assert [x['rank'] for x in bat] == list(range(1, 11))
    assert [x['rank'] for x in bowl] == list(range(1, 11))


def test_scope_counts_are_consistent():
    payload = json.loads((DATA / 'dashboard.json').read_text(encoding='utf-8'))
    scope = payload['scope']
    assert scope['match_count'] == scope['ipl_match_count'] + scope['t20i_match_count']
    assert 0 < scope['pressure_delivery_count'] < scope['delivery_count']
    assert scope['pressure_match_count'] <= scope['match_count']


def test_csv_exports_have_ten_rows():
    for filename in ['top10_batters.csv', 'top10_bowlers.csv']:
        with (DATA / filename).open(newline='', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 10


def test_private_source_zip_is_not_in_public_site():
    assert not (ROOT / 'data' / 'private' / 'organizer_data_pack.zip').exists()
    assert (ROOT / 'data' / 'private' / 'README.md').exists()
