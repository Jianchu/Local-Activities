# Near & Now

A mobile-friendly Surrey + Richmond activity finder. Plain HTML, CSS and JavaScript with a Python data collector; no frontend build step or application secrets.

## Deploy on Vercel

1. Open https://vercel.com/new and import `Jianchu/Local-Activities`.
2. Use **Other** as the framework, leave the build command empty, and use **public** as the output directory (`vercel.json` also declares it).
3. Deploy. Set `main` as the production branch. Future pushes trigger deployment through Vercel's GitHub integration.

The repository is ready for import; a Vercel account connection must be completed by the owner. No deployment URL is claimed until this is done.

## Data

`public/data/events.json` is a committed, cached snapshot. GitHub Actions refreshes it daily at 13:23 UTC and can also be run from **Actions → Refresh city activities → Run workflow**. It commits changes to the default branch. GitHub schedule execution can be delayed; the UI flags data older than 48 hours. Check that Vercel is deploying the automated data commits after connecting it.

The collector follows Surrey's server-rendered calendar pagination and individual detail pages. Richmond's ASP.NET calendar requires form state for date selection and pagination; its detail pages supply descriptions and venues. These are public website interfaces, not guaranteed public APIs. They may change. No credentials are sent to either city.

- A session is a published event occurrence or date range. Date-range listings are not expanded into assumed daily occurrences.
- Time-of-day filtering checks published time intervals. Listings with no usable time are excluded when a time-of-day filter is selected.
- Some organizers publish times/venues only on linked booking pages; missing times are marked explicitly, never invented.
- Categories are inferred from official categories and titles; original category text is retained in the data.
- Multi-date tables are used for per-session venues when available.
- On source failure, the last successful data for that city is retained and flagged. Source freshness appears on the site.
- The calendar is not a complete inventory of registered recreation courses. Follow source links for current schedules, costs, availability and registration.

## Local development

```sh
pip install -r requirements.txt
python scripts/collect.py
python -m unittest discover -s tests
node --check public/app.js
python -m http.server 8000 --directory public
```

Open http://localhost:8000. Use Python 3.12+. On systems without an IANA timezone database, install `tzdata`.

Design: warm off-white surfaces, forest-green controls, category-tinted cards, responsive layout, keyboard-accessible filters, and reduced-motion support. Source text is escaped before rendering; source HTML is never injected into the UI.
