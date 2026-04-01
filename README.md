# RICCE Ontology Explorer

Public-safe ontology starter for Firebase Hosting.

It also supports GitHub Pages for the three static entry points:

- ontology explorer
- grants.gov explorer
- SAM.gov explorer

This repo is distilled for public access:

- fictional sample data only
- no private intake files
- no local-only evidence folders
- no canonical operator scratch files
- optional local-only preview flow for your own private CSV
- grants.gov and SAM.gov file-picker workbenches with harmless sample feeds

## What this repo is for

- relationship mapping by `Name`, `Organization`, and `Service Area`
- demo deployments with sample data
- local private preview of your own sanitized dataset
- public-sector opportunity exploration from locally downloaded XML and CSV files

## License

This repo uses the MIT License. MIT allows reuse, modification, sublicensing, and distribution as long as the copyright notice and license text stay with the software.

Attribution note:

- Legal requirement: keep the MIT license notice with redistributed copies or substantial portions.
- Courtesy request: if you reuse or adapt this project, crediting `yagaC64` / RICCE in your docs, credits, or repository notes is appreciated.

## Launcher strategy

This repo avoids duplicated launcher logic across operating systems:

- `run.sh`: thin macOS/Linux launcher
- `run.ps1`: thin Windows PowerShell launcher
- `scripts/run_menu.py`: shared cross-platform bootstrap and operator menu
- `scripts/security_checks.py`: shared cross-platform preflight checks

## Clone and run locally

macOS / Linux:

```bash
git clone https://github.com/yagaC64/AI_class_public_repo.git
cd AI_class_public_repo
chmod +x run.sh scripts/*.sh .githooks/pre-commit
./run.sh
```

Windows PowerShell:

```powershell
git clone https://github.com/yagaC64/AI_class_public_repo.git
cd AI_class_public_repo
.\run.ps1
```

Then:

1. Choose `1` to run preflight checks.
2. Choose `2` to start the sample site.
3. Open `http://127.0.0.1:8000/` if the browser does not open automatically.

## Manual local run

```bash
python3 -m http.server 8000 --bind 127.0.0.1 --directory public
```

Then open:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/tools/grants_gov.html`
- `http://127.0.0.1:8000/tools/sam_gov.html`

## GitHub Pages

This repo now includes a GitHub Actions workflow that deploys the tracked `public/` bundle to GitHub Pages from `main`.

One-time setup in GitHub:

1. Push the repo with `.github/workflows/deploy-pages.yml` on `main`.
2. In the GitHub repo, open `Settings` -> `Pages`.
3. Under `Build and deployment`, set `Source` to `GitHub Actions`.
4. Push to `main` again if needed, or run the `Deploy GitHub Pages` workflow from the `Actions` tab.

If the repo owner remains `yagaC64` and the repo name remains `AI_class_public_repo`, the Pages URLs are:

- Ontology explorer: `https://yagaC64.github.io/AI_class_public_repo/`
- Grants.gov explorer: `https://yagaC64.github.io/AI_class_public_repo/tools/grants_gov.html`
- SAM.gov explorer: `https://yagaC64.github.io/AI_class_public_repo/tools/sam_gov.html`

Notes:

- The GitHub Pages deployment is public-safe and sample-first.
- `public/data/local/` stays local-only and is not part of the tracked Pages deployment.
- Firebase Hosting still works; the app now resolves asset and dataset paths correctly under both root hosting and a repo subpath.

## Use your own private data locally

1. Put your curated CSV at `data/private/ricce-ontology-master.csv`.
2. Run:

   ```bash
   ./scripts/publish_public_data.sh
   ```

3. Start the local server with `./run.sh` option `4`, or `.\run.ps1` on Windows.
4. Open:

   - `http://127.0.0.1:8000/?csv=data/local/ricce-ontology-private-preview.csv`

That query-string override is local-only. Do not point a public deployment at that path.

## Public sample files

- Main app sample feed: `public/data/ricce-ontology-sample.csv`
- Main app sample manifest: `public/data/ricce-ontology-sample.manifest.json`
- Grants sample feed: `public/tools/examples/grants-opportunities-sample.xml`
- SAM sample feed: `public/tools/examples/sam-contract-opportunities-sample.csv`

## Data sources

Official starting points verified on March 31, 2026:

- Grants.gov home: [https://www.grants.gov/](https://www.grants.gov/)
- Grants.gov XML extract page: [https://www.grants.gov/xml-extract](https://www.grants.gov/xml-extract)
- SAM.gov contracting entry point: [https://sam.gov/contracting](https://sam.gov/contracting)
- SAM.gov Contract Opportunities data page: [https://sam.gov/data-services/Contract%20Opportunities?privacy=Public](https://sam.gov/data-services/Contract%20Opportunities?privacy=Public)
- SAM.gov Contract Opportunities Data Bank export page: [https://sam.gov/data-services/Contract%20Opportunities/datagov?privacy=Public](https://sam.gov/data-services/Contract%20Opportunities/datagov?privacy=Public)

## Repo layout

- `public/`: deployable public-safe site
- `public/data/`: fictional sample data
- `public/tools/`: grants.gov and SAM.gov explorers
- `data/private/`: your own local-only curated CSV goes here
- `data/raw/`: your own local-only intake files go here
- `integrations/google-apps-script/`: optional Google Sheets + Apps Script bridge
- `scripts/`: local preview, deploy, and preflight tooling

## Local operator commands

- `./run.sh`
- `.\run.ps1`
- `python scripts/run_menu.py status`
- `./scripts/security-checks.sh`
- `python scripts/security_checks.py`
- `./scripts/publish_public_data.sh`
- `./scripts/deploy_hosting_safe.sh`
- `./scripts/preview_hosting_safe.sh`

## Notes

- This repo intentionally ships with no PII and no private data files.
- `public/data/local/` is gitignored and excluded from Firebase Hosting.
- If you switch to Apps Script mode, keep the backend response limited to the public-safe fields only.
