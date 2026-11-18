$ErrorActionPreference = 'Stop'

Write-Host 'Installing Python requirements...'
python -m pip install -r requirements.txt

Write-Host 'Rebuilding rankings from data/private/organizer_data_pack.zip...'
python analysis/build_rankings.py

Write-Host 'Done. Review app/data/dashboard.json and the CSV exports.'
