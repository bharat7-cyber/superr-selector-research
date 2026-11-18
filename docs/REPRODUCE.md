# Rebuild and publish

## Local analysis rebuild

1. Download the original data pack from Unstop > Brief/Case.
2. Place it at `data/private/organizer_data_pack.zip`.
3. Install Python 3.10+ and project dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Run the pipeline (`./run_analysis.ps1` also works in PowerShell):

   ```bash
   python analysis/build_rankings.py
   ```

5. Review `app/data/analysis_audit.json`, `app/data/top10_batters.csv`, `app/data/top10_bowlers.csv` and `app/data/dashboard.json`.
6. Run the website locally (`./start_website.ps1` also works in PowerShell):

   ```bash
   python -m http.server 8000 --directory app
   ```

   Open `http://localhost:8000`.

## GitHub Pages deployment

1. Create a new GitHub repository (for example, `superr-pressure-analysis`).
2. Upload the project contents. **Do not upload the organiser ZIP or raw CSVs.** The `data/private/` folder is git-ignored.
3. Push the `main` branch.
4. In GitHub, open **Settings → Pages** and set the source to **GitHub Actions**.
5. The included workflow `.github/workflows/pages.yml` builds and deploys the static `app/` directory.
6. The public dashboard link will be `https://YOUR-USERNAME.github.io/REPOSITORY-NAME/`.

The site uses relative asset paths so it works under a GitHub Pages project URL.

## Before submitting

- Make sure the Unstop dropdown rankings match the website rankings.
- Explain the pressure definition and weights in your own words.
- Do not claim any player is auction-registered or available unless checked against the official registered-player list.
- Do not publish the organiser data pack or raw CSV files.
