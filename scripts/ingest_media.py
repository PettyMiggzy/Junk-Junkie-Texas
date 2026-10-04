#!/usr/bin/env python3
"""Sort real job photos across the 4 Texas sites (each site gets its own set).
Usage: python3 scripts/ingest_media.py /path/to/optimized/webp/folder
Writes data/<site>/{reel,photos}/ and data/<site>/jobs.json (seed gallery cards, no invented locations/dates)."""
import sys, json, os, shutil
from pathlib import Path
from PIL import Image

SRC = Path(sys.argv[1]); ROOT = Path(__file__).resolve().parent.parent
SITES = ["spring", "tomball", "cypress", "college-station"]
JR, LM, FR, DR = "Junk Removal", "Local Moving", "Furniture Removal", "Debris Removal"
D = {
 JR: "Loaded up and hauled away in one trip. We sweep up when we are done.",
 LM: "Wrapped, padded and loaded so it arrives without a scratch. We handle the heavy lifting.",
 FR: "Picked up and hauled off. No lifting or loading on your end.",
 DR: "Debris cleared out and hauled away so the space is ready to use.",
}
# number -> (title, service)
C = {
 "005": ("Trailer loaded and ready to roll", JR), "006": ("Storage unit cleanout", JR), "008": ("Recliner ready for pickup", FR),
 "009": ("Furniture wrapped for a safe move", LM), "010": ("Wrapped piece on its way out", LM), "011": ("Refrigerator prepped for the move", LM),
 "013": ("Large pieces wrapped and protected", LM), "016": ("Lumber and tarp debris cleared", DR), "017": ("Trailer loaded and ready", JR),
 "019": ("Bagged-up room cleanout", JR), "020": ("Sectional couch ready for pickup", FR), "021": ("Cabinet wrapped for transport", LM),
 "022": ("Wrapped furniture ready to move", LM), "023": ("Refrigerator ready to go", LM), "025": ("Job-site debris cleared out", DR),
 "026": ("Crew carrying a large item to the trailer", JR), "027": ("Table wrapped and loaded in the trailer", LM), "030": ("Curbside pile hauled away", JR),
 "032": ("Truck packed with wrapped furniture", LM), "033": ("Couch loaded on the trailer", FR), "034": ("Sectional wrapped for the move", LM),
 "035": ("Wrapped furniture on the hand truck", LM), "037": ("Truck loaded with boxes and furniture", LM), "038": ("Carrying furniture down the stairs", LM),
 "039": ("Kitchen packed up for the move", LM), "040": ("Appliances wrapped and secured in the trailer", LM), "041": ("Trailer packed floor to ceiling", LM),
 "043": ("Truck and trailer on the job", JR), "044": ("Driveway pile hauled away", JR), "047": ("Crew at work on a driveway job", JR),
 "048": ("Couch on the trailer", FR), "049": ("Dresser wrapped for transport", LM), "050": ("Sectional couch ready for pickup", FR),
 "052": ("Hand trucks and wrapped pieces", LM), "053": ("Yard junk pile ready to haul", JR), "054": ("Garage cleanout pile", JR),
 "057": ("Curbside furniture and junk hauled off", JR), "058": ("Recliner ready for pickup", FR), "059": ("Dresser wrapped and protected", LM),
 "060": ("Crew member on a job", LM), "061": ("Upright piano ready to move", LM), "062": ("Lumber and decking debris hauled away", DR),
 "065": ("Yard bags ready to haul", JR), "074": ("Desk ready for pickup", FR), "075": ("Dining set ready for pickup", FR),
 "077": ("Backyard shed ready for removal", JR), "078": ("Truck and trailer ready to roll", JR), "079": ("Trailer loaded with boxes and fabric", JR),
 "086": ("Trailer ready for a haul", JR), "sda": ("Trailer packed with boxes and wrapped furniture", LM),
}
def num(p): return p.stem.replace("junkjunkies_", "")
files = sorted(p for p in SRC.glob("*.webp") if num(p) in C)
land = [p for p in files if Image.open(p).size[0] > Image.open(p).size[1]]
port = [p for p in files if p not in land]
for s in SITES:
    for sub in ("reel", "photos"):
        d = ROOT / "data" / s / sub
        if d.exists(): shutil.rmtree(d)
        d.mkdir(parents=True)
jobs = {s: [] for s in SITES}
def put(p, site, kind, maxdim, q):
    im = Image.open(p).convert("RGB"); sc = min(1, maxdim / max(im.size)); im = im.resize((int(im.size[0]*sc), int(im.size[1]*sc)), Image.LANCZOS)
    name = f"jj-{num(p)}.webp"; im.save(ROOT / "data" / site / kind / name, quality=q, method=6); return name
# every photo goes to exactly ONE site (round-robin so each site gets a mix); each site's first 5 landscape
# photos become its hero reel, everything else is its gallery. No photo repeats across sites.
mine = {s: [] for s in SITES}
for i, p in enumerate(files): mine[SITES[i % 4]].append(p)
for site in SITES:
    PRI = ["043", "078", "017", "086", "057", "054", "053", "062", "030", "044"]   # outdoor truck/trailer shots lead the reel
    cand = sorted([p for p in mine[site] if p in land], key=lambda p: (PRI.index(num(p)) if num(p) in PRI else 99, num(p)))
    ls = cand[:5]
    for r, p in enumerate(ls):
        n = put(p, site, "reel", 1600, 78); (ROOT/"data"/site/"reel"/n).rename(ROOT/"data"/site/"reel"/f"{r}-{n}")
    for p in mine[site]:
        if p in ls: continue
        n = put(p, site, "photos", 1100, 78); t, svc = C[num(p)]
        jobs[site].append({"title": t, "service": svc, "description": D[svc], "after_url": f"/assets/jobs/{n}"})
for s in SITES: json.dump(jobs[s], open(ROOT / "data" / s / "jobs.json", "w"), indent=1)
for s in SITES: print(s, "reel:", len(list((ROOT/'data'/s/'reel').glob('*'))), "gallery:", len(jobs[s]))
