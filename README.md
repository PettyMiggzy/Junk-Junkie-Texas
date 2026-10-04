# Junk Junkies Texas: 4 sites, 1 codebase

| Site | Cities | Config |
|---|---|---|
| Spring (junkjunkiestexas.com) | Spring, Klein, The Woodlands, Humble | `sites/spring.json` |
| Tomball | Tomball, Magnolia, Pinehurst | `sites/tomball.json` |
| Cypress | Cypress, Jersey Village, Hockley | `sites/cypress.json` |
| College Station | College Station, Bryan, Navasota | `sites/college-station.json` |

All sites: (346) 413-9644, forms to junkjunkiestexas@gmail.com.

## Edit
- Phone/email/domain/Web3Forms key: `sites/<site>.json`
- City + service copy (unique per city; keep it unique for SEO): `content.py`
- Look and layout (all 4 at once): `build.py`, `tools/input.css`
- Reviews: `data/<site>/reviews.json`  `[{"author","rating","text","area"}]` (shows only if filled, never fake)
- Completed jobs on the map: `data/<site>/jobs.json`  `[{"title","area","lat","lon","image"}]`; put photos in `data/<site>/photos/` and use `/assets/jobs/<file>`
- Logos: `assets/logos/<site>.png`

## Build
```
pip install pillow numpy
cd tools && npm install && cd ..
bash build.sh            # all sites -> dist/<site>/   (or: bash build.sh spring)
```
Commit `dist/`. No build step is needed on Vercel.

## Deploy (4 Vercel projects, same repo)
For each site: Add New Project > this repo > Framework **Other** > Root Directory `dist/<site>` > no build command. Then add the site's domain.

## Live features (need one-time setup per Vercel project)
- **Completed jobs map + gallery (`/our-work/`)** and **crew upload (`/crew/`)**: crew open `/crew/` on a phone, enter the PIN, snap before/after photos, and the job appears on the map. Needs Vercel env vars: `DATABASE_URL` (Neon Postgres), `BLOB_READ_WRITE_TOKEN` (Vercel Blob store connected to the project), `CREW_PIN` (a number you pick). The table creates itself.
- **Google reviews**: env vars `GOOGLE_PLACES_KEY` (Google Cloud, Places API (New) enabled) and `GOOGLE_PLACE_ID` (the location's Place ID). Shows up to 5 recent 4-5 star reviews (Google's limit) plus the rating and count; cached 24h.
- Until those are set the pages work normally and the job/review sections stay empty or hidden.
- Job pins are rounded to ~1 km so a customer's exact address is never published.
- Hero photo reel: add JPG/WEBP files to `data/<site>/reel/` and rebuild.

## Hosting status
- Vercel projects: `junkjunkies-spring`, `junkjunkies-tomball`, `junkjunkies-cypress`, `junkjunkies-college-station` (root dir `dist/<site>`, production branch `main`).
- Shared Neon database `junkjunkies` (limited role `junkjunkies_app`); every job row has a `site` column. One Blob store per project.
- `DATABASE_URL`, `CREW_PIN`, `BLOB_READ_WRITE_TOKEN` are set in each Vercel project. `GOOGLE_PLACES_KEY` is set on all projects; `GOOGLE_PLACE_ID` is set on Spring (ChIJt1oNIK6RSYYRSdYZxMjE2tk). Tomball, Cypress and College Station need their own Place IDs once those Google profiles exist.
- `junkjunkiestexas.com` is intentionally NOT attached yet (live WordPress site).
