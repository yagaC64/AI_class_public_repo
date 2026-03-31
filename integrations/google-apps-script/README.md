# Google Apps Script bridge

This folder scaffolds the no-cost backend pattern for this repo: Firebase Hosting serves the app, while Google Sheets plus an Apps Script Web App can serve the publish-safe profile dataset when you are ready to move beyond local CSV deployment.

## What this script does

- Reads the `Records` sheet from a Google Sheet identified by the `RICCE_SHEET_ID` script property
- Publishes only the fields needed by the public graph:
  - `Name`
  - `Organization`
  - `Service Area`
- Deduplicates exact duplicates and drops incomplete rows
- Supports:
  - `?mode=records`
  - `?mode=health`

## Recommended Google Sheet tabs

- `Records`
- `AuditLog`
- optionally `Config`

The `Records` tab can either keep the current imported long header `Service Area of the Non-Profit Organization` or a shortened `Service Area` header. The script handles both.

## Setup

1. Create or choose the protected Google Sheet that will hold the curated dataset.
2. Add a `Records` tab and import the curated data.
3. Create a standalone Apps Script project.
4. Copy in `Code.gs` and `appsscript.json`.
5. In Apps Script, open `Project Settings` and set a script property:
   - `RICCE_SHEET_ID=<your-google-sheet-id>`
6. Deploy as a Web App:
   - Execute as: `Me`
   - Who has access: `Anyone`
7. Copy the deployed Web App URL into `public/assets/js/site-config.js` and switch:
   - `dataMode: "apps_script"`

## Validation

- Visit `WEB_APP_URL?mode=health`
- Visit `WEB_APP_URL?mode=records`
- Confirm the payload contains only the three public fields

## Security notes

- Do not expose admin-only columns in the `Code.gs` response.
- Keep Google Sheet access limited to named admins.
- Treat the Apps Script endpoint as public-read for only the publish-safe fields.
