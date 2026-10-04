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
