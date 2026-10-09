#!/usr/bin/env python3
"""Builds all Junk Junkies Texas sites from one template.
Usage: python3 build.py [site-slug ...]   (default: all)  -> dist/<slug>/
Then: bash build.sh  (also compiles CSS)."""
import json, sys, shutil, datetime
from pathlib import Path
from content import CITIES, SERVICES

ROOT = Path(__file__).parent
TODAY = datetime.date.today().isoformat()
YEAR = datetime.date.today().year
SITES = {p.stem: json.loads(p.read_text()) for p in sorted((ROOT / "sites").glob("*.json"))}
ROUTES = json.loads((ROOT / "shared" / "routes.json").read_text())
HOME_SERVICES = [s["name"] for s in SERVICES]

ROUTES_JS = """// GENERATED from shared/routes.json by build.py. Do not edit.
const SITES = """ + json.dumps(ROUTES) + """;
const rad = d => d * Math.PI / 180;
function miles(a, b, c, d) { const x = Math.sin(rad(c - a) / 2) ** 2 + Math.cos(rad(a)) * Math.cos(rad(c)) * Math.sin(rad(d - b) / 2) ** 2; return 3958.8 * 2 * Math.asin(Math.sqrt(x)); }
// Nearest service city to a GPS point; null if farther than maxMiles from every city.
export function nearest(lat, lon, maxMiles = 45) {
  let best = null;
  for (const [site, s] of Object.entries(SITES)) for (const [city, la, lo] of s.cities) { const d = miles(lat, lon, la, lo); if (!best || d < best.miles) best = { site, siteName: s.name, city, miles: d }; }
  return best && best.miles <= maxMiles ? best : null;
}
"""

def jload(p, default):
    try: return json.loads(Path(p).read_text())
    except Exception: return default

class Site:
    def __init__(self, cfg):
        self.c = cfg; self.slug = cfg["slug"]; self.base = "https://" + cfg["domain"]
        self.hub = CITIES[cfg["hub"]]; self.cities = [CITIES[s] for s in cfg["cities"]]
        self.is_hq = cfg["slug"] == "spring"
        self.out = ROOT / "dist" / self.slug
        self.reviews = jload(ROOT / "data" / self.slug / "reviews.json", [])
        self.jobs = jload(ROOT / "data" / self.slug / "jobs.json", [])   # optional hand-curated seed jobs
        rd = ROOT / "data" / self.slug / "reel"
        self.reel = [f"/assets/reel/{x.name}" for x in sorted(rd.glob("*")) if x.suffix.lower() in (".jpg", ".jpeg", ".webp")] if rd.exists() else []
        self.biz_id = self.base + "/#business"
        self.og = self.base + "/assets/og-image.jpg"
    def svc_path(self, s): return f"/{s['slug']}-{self.c['hub']}-tx/"
    def city_path(self, c): return f"/{[k for k,v in CITIES.items() if v is c][0]}-junk-removal/"
    def write(self, path, html):
        p = self.out / path.strip("/") / "index.html" if path != "/" else self.out / "index.html"
        p.parent.mkdir(parents=True, exist_ok=True); p.write_text(html)

# ------------------------------------------------------------ schema
def ld(*objs): return "".join(f'<script type="application/ld+json">{json.dumps(o, separators=(",", ":"))}</script>' for o in objs)

def business_schema(S):
    c = S.c
    addr = {"@type": "PostalAddress", "addressLocality": S.hub["name"], "addressRegion": "TX", "addressCountry": "US"}
    if S.is_hq: addr.update({"streetAddress": c["street"], "postalCode": c["zip"], "addressLocality": c["street_city"]})
    sameas = [f"https://{o['domain']}" for k, o in SITES.items() if k != S.slug and not o.get("domain_is_placeholder")]
    return {"@context": "https://schema.org", "@type": ["LocalBusiness", "HomeAndConstructionBusiness"], "@id": S.biz_id,
        "name": c["name"], "url": S.base + "/", "image": S.og, "logo": f"{S.base}/assets/logo.png", "telephone": c["phone_tel"], "email": c["email"],
        "description": f"Junk removal, debris removal, hoarder cleanouts and appliance removal in {', '.join(x['name'] for x in S.cities)}, Texas.",
        "address": addr, "geo": {"@type": "GeoCoordinates", "latitude": S.hub["lat"], "longitude": S.hub["lon"]},
        "areaServed": [{"@type": "City", "name": x["name"] + ", TX"} for x in S.cities], "sameAs": sameas,
        "contactPoint": {"@type": "ContactPoint", "telephone": c["phone_tel"], "contactType": "customer service", "areaServed": "US-TX", "availableLanguage": "English"}}
def faq_schema(faq): return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}
def crumbs(S, items): return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i+1, "name": n, "item": S.base + u} for i, (n, u) in enumerate(items)]}

# ------------------------------------------------------------ layout
def head(S, title, desc, path, schema="", extra=""):
    u = S.base + path
    gid = S.c.get("gtag_id", "")
    gtag = (f'<!-- Google tag (gtag.js) --><script async src="https://www.googletagmanager.com/gtag/js?id={gid}"></script><script>window.dataLayer = window.dataLayer || [];function gtag(){{dataLayer.push(arguments);}}gtag(\'js\', new Date());gtag(\'config\', \'{gid}\');</script>') if gid and "noindex" not in extra else ""
    return f'''<!DOCTYPE html><html lang="en-US"><head>{gtag}<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title><meta name="description" content="{desc}"><link rel="canonical" href="{u}">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1"><meta name="theme-color" content="#0B0D10"><meta name="geo.region" content="US-TX"><meta name="geo.placename" content="{S.hub['name']}">
<meta property="og:type" content="website"><meta property="og:site_name" content="{S.c['name']}"><meta property="og:locale" content="en_US"><meta property="og:title" content="{title}"><meta property="og:description" content="{desc}"><meta property="og:url" content="{u}">
<meta property="og:image" content="{S.og}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{title}"><meta name="twitter:description" content="{desc}"><meta name="twitter:image" content="{S.og}">
<link rel="icon" href="/favicon.ico?v=3" sizes="any"><link rel="icon" type="image/png" sizes="192x192" href="/favicon-192.png?v=3"><link rel="icon" type="image/png" href="/favicon.png?v=3"><link rel="apple-touch-icon" href="/assets/logo-icon.png?v=2"><link rel="manifest" href="/site.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=Inter:wght@400;500;600&display=swap"><link rel="stylesheet" href="/assets/site.css">{extra}{schema}</head><body class="antialiased">'''

def header(S):
    c = S.c
    return f'''<header class="fixed top-0 inset-x-0 z-50 backdrop-blur-md bg-ink/80 border-b border-line"><div class="max-w-7xl mx-auto px-5 h-16 flex items-center justify-between">
<a href="/" class="flex items-center gap-2.5"><img src="/assets/logo-badge.png" width="56" height="56" alt="{c['name']} logo" class="h-14 w-14 rounded-xl logo-pulse"><span class="display block max-w-[11rem] sm:max-w-none text-[11px] sm:text-base font-extrabold leading-[1.15]">{S.c['name']}</span></a>
<nav class="hidden md:flex items-center gap-8 text-sm text-bone/70" aria-label="Main"><a href="/services/" class="hover:text-bone">Services</a><a href="/areas/" class="hover:text-bone">Service Areas</a><a href="/our-work/" class="hover:text-bone">Our Work</a><a href="/#faq" class="hover:text-bone">FAQ</a></nav>
<div class="flex items-center gap-3"><a href="tel:{c['phone_tel']}" class="hidden sm:inline-flex text-sm font-semibold text-bone/90 hover:text-ember">{c['phone_display']}</a><a href="#quote" class="inline-flex whitespace-nowrap rounded-full bg-ember hover:bg-emberDark text-ink font-bold text-sm px-4 sm:px-5 py-2.5 transition">Free Quote</a></div></div></header>'''

def footer(S):
    c = S.c
    cities = "".join(f'<a href="{S.city_path(x)}" class="block text-bone/60 hover:text-ember py-0.5">{x["name"]}</a>' for x in S.cities)
    svcs = "".join(f'<a href="{S.svc_path(s)}" class="block text-bone/60 hover:text-ember py-0.5">{s["name"]}</a>' for s in SERVICES)
    sis = "".join(f'<a rel="noopener" href="https://{o["domain"]}" class="block text-bone/60 hover:text-ember">{o["name"]}</a>' for k, o in SITES.items() if k != S.slug and not o.get("domain_is_placeholder"))
    addr = f'<address class="not-italic text-bone/60 mt-2">{c["street"]}<br>{c["street_city"]}, TX {c["zip"]}</address>' if S.is_hq else ""
    return f'''<footer class="border-t border-line py-16 pb-32 md:pb-16"><div class="max-w-7xl mx-auto px-5 grid md:grid-cols-4 gap-10 text-sm">
<div><img src="/assets/logo.png" width="160" height="160" alt="{c['name']} junk removal logo" class="h-40 w-40 mb-4" loading="lazy"><p class="text-bone/50">Junk removal in {", ".join(x["name"] for x in S.cities)}, Texas. Veteran and first responder discount available.</p></div>
<div><div class="font-semibold mb-3">Services</div>{svcs}</div><div><div class="font-semibold mb-3">Service Areas</div>{cities}</div>
<div><div class="font-semibold mb-3">Contact</div><a href="tel:{c['phone_tel']}" class="block text-bone/60 hover:text-ember">{c['phone_display']}</a><a href="sms:{c['phone_tel']}" class="block text-bone/60 hover:text-ember">Text us photos</a><a href="mailto:{c['email']}" class="block text-bone/60 hover:text-ember">{c['email']}</a>{addr}
{('<div class="mt-6 font-semibold mb-3">Our other locations</div>'+sis) if sis else ''}</div></div>
<div class="max-w-7xl mx-auto px-5 mt-12 text-xs text-bone/40">© {YEAR} {c['name']}. All rights reserved.</div></footer>
<div class="md:hidden fixed bottom-0 inset-x-0 z-50 bg-ink/95 backdrop-blur border-t border-line grid grid-cols-3 text-center text-sm font-bold"><a href="tel:{c['phone_tel']}" class="py-4 border-r border-line">Call</a><a href="sms:{c['phone_tel']}?body=Hi%2C%20I%20need%20a%20junk%20removal%20quote" class="py-4 border-r border-line">Text</a><a href="#quote" class="py-4 bg-ember text-ink">Quote</a></div>
<script src="/assets/form.js" defer></script><script src="/assets/app.js" defer></script></body></html>'''

def quote_form(S, place, anchor="quote-more"):
    c = S.c; inp = 'bg-ink border border-line rounded-xl px-4 py-3 w-full focus:outline-none focus:border-ember'
    opts = "".join(f"<option>{o}</option>" for o in HOME_SERVICES)
    return f'''<section id="{anchor}" class="py-20 bg-slate2 border-y border-line"><div class="max-w-5xl mx-auto px-5 grid lg:grid-cols-2 gap-10">
<div><p class="text-xs font-semibold tracking-widest uppercase text-ember mb-4">Free quote</p><h2 class="display text-3xl md:text-4xl font-extrabold leading-tight mb-4">Get a fast quote for {place}.</h2>
<p class="text-bone/60 mb-4">Tell us what you need hauled and we will text you a price. Or call <a class="text-ember font-semibold" href="tel:{c['phone_tel']}">{c['phone_display']}</a>, or text photos to the same number.</p>
<p class="text-sm text-ember font-semibold">★ Veteran and first responder discount available</p></div>
<form data-quote class="grid sm:grid-cols-2 gap-3" aria-label="Quote request" data-key="{c['web3forms_key']}" data-email="{c['email']}" data-site="{c['name']}">
<input type="hidden" name="access_key" value="{c['web3forms_key']}"><input type="hidden" name="subject" value="Quote request: {S.c['name']} ({place})"><input type="hidden" name="from_name" value="{c['name']} website"><input type="checkbox" name="botcheck" style="display:none">
<input required name="first_name" aria-label="First name" placeholder="First name" class="{inp}"><input required name="last_name" aria-label="Last name" placeholder="Last name" class="{inp}">
<select required name="service" aria-label="Service" class="{inp} sm:col-span-2"><option value="">Choose service</option>{opts}</select>
<input required name="phone" type="tel" aria-label="Phone" placeholder="Phone number" class="{inp}"><input required name="email" type="email" aria-label="Email" placeholder="Email" class="{inp}">
<input required name="address" aria-label="Address" placeholder="Address" class="{inp} sm:col-span-2"><input required name="city" aria-label="City" placeholder="City" class="{inp}"><input required name="zip" aria-label="Zip" placeholder="Zip code" class="{inp}">
<label class="block text-sm text-bone/70 sm:col-span-2">📷 Add photos for the fastest firm price <span class="text-bone/40">(optional)</span><input type="file" name="photos" accept="image/*" multiple class="mt-1 block w-full text-sm"></label>
<textarea name="message" rows="3" aria-label="Message" placeholder="Message (optional)" class="{inp} sm:col-span-2"></textarea>
<button type="submit" data-btn class="sm:col-span-2 rounded-full bg-ember hover:bg-emberDark text-ink font-bold px-8 py-4 transition">Get My Fast Quote</button><p data-msg class="sm:col-span-2 text-sm text-center text-bone/60" role="status"></p></form></div></section>'''

def top_form(S, place, anchor=True):
    c = S.c; inp = 'bg-ink border border-line rounded-xl px-4 py-2 sm:py-3 w-full text-base focus:outline-none focus:border-ember'
    opts = "".join(f"<option>{o}</option>" for o in HOME_SERVICES)
    return f"""<div {'id="quote" ' if anchor else ''}class="rounded-3xl bg-slate2/90 backdrop-blur border border-line p-4 sm:p-6 shadow-2xl scroll-mt-24">
<div class="display text-lg sm:text-2xl font-extrabold leading-tight">Get your free quote in minutes</div>
<p class="hidden sm:block text-sm text-bone/60 mt-1 mb-2">Tell us what you need. We'll text you a price.</p>
<div class="disc mt-2 mb-3 sm:mb-4" role="note" aria-label="10 percent discount for veterans, seniors and first responders"><div class="disc-badge" aria-hidden="true"><span>10%</span></div><div class="disc-txt"><b>10% OFF</b><span>Veterans, seniors &amp; first responders</span></div><svg class="disc-ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2l2.9 6.3 6.9.8-5.1 4.7 1.4 6.8L12 17.3 5.9 20.6l1.4-6.8L2.2 9.1l6.9-.8z"/></svg></div>
<form data-quote class="grid gap-3" aria-label="Quick quote request" data-key="{c['web3forms_key']}" data-email="{c['email']}" data-site="{c['name']}">
<input type="hidden" name="access_key" value="{c['web3forms_key']}"><input type="hidden" name="subject" value="Quote request: {c['name']} ({place})"><input type="hidden" name="from_name" value="{c['name']} website"><input type="checkbox" name="botcheck" style="display:none">
<input required name="name" autocomplete="name" aria-label="Your name" placeholder="Your name" class="{inp}">
<input required name="phone" type="tel" inputmode="tel" autocomplete="tel" aria-label="Phone number" placeholder="Phone number" class="{inp}">
<div class="grid grid-cols-5 gap-3"><input required name="zip" inputmode="numeric" autocomplete="postal-code" aria-label="Zip code" placeholder="Zip" class="{inp} col-span-2"><select name="service" aria-label="What do you need" class="{inp} col-span-3"><option value="">Service needed</option>{opts}</select></div>
<label class="block text-sm text-bone/70">📷 Add photos for the fastest firm price <span class="text-bone/40">(optional)</span><input type="file" name="photos" accept="image/*" multiple class="mt-1 block w-full text-sm"></label>
<textarea name="message" rows="1" maxlength="600" aria-label="Notes" placeholder="Notes (optional)" class="{inp} resize-none"></textarea>
<button type="submit" data-btn class="rounded-full bg-ember hover:bg-emberDark text-ink font-bold px-8 py-3 sm:py-4 text-base transition glow">Get My Free Quote</button>
<p data-msg class="text-sm text-center text-bone/60" role="status"></p></form>
<div class="text-center text-sm text-bone/60">or call / text <a class="text-ember font-semibold" href="tel:{c['phone_tel']}">{c['phone_display']}</a> with photos</div></div>"""

def faq_html(faq): return '<div class="divide-y divide-line">' + "".join(f'<details class="py-5 group"><summary class="display font-bold text-lg cursor-pointer list-none flex justify-between gap-4">{q}<span class="text-ember group-open:rotate-45 transition">+</span></summary><p class="text-bone/60 mt-3">{a}</p></details>' for q, a in faq) + "</div>"
def crumb_html(parts):
    out = [f'<a href="{u}" class="hover:text-ember">{n}</a>' if i < len(parts)-1 else f'<span class="text-bone/80">{n}</span>' for i, (n, u) in enumerate(parts)]
    return '<nav aria-label="Breadcrumb" class="text-xs text-bone/50 mb-6 flex flex-wrap gap-2">' + ' <span>/</span> '.join(out) + "</nav>"
def hero_small(S, h1, sub, crumbs_html, place=None):
    c = S.c; place = place or (S.hub["name"] + ", TX")
    return f"""<section class="relative pt-24 pb-10 md:pt-32 md:pb-16 overflow-hidden"><img src="/assets/hero.webp" width="1280" height="720" alt="" class="absolute inset-0 w-full h-full object-cover opacity-30"><div class="absolute inset-0 bg-gradient-to-t from-ink via-ink/85 to-ink/40"></div>
<div class="relative max-w-6xl mx-auto px-5 grid lg:grid-cols-12 gap-8 items-start"><div class="lg:col-span-7">{crumbs_html}<h1 class="display text-3xl sm:text-5xl lg:text-6xl font-extrabold leading-[1.03] mb-4">{h1}</h1><p class="hidden sm:block text-base md:text-xl text-bone/75 max-w-2xl mb-6">{sub}</p>
<div class="hidden sm:flex flex-col sm:flex-row gap-3"><a href="tel:{c['phone_tel']}" class="inline-flex justify-center rounded-full border border-bone/25 hover:border-bone/60 font-semibold px-8 py-4 transition">Call {c['phone_display']}</a></div></div>
<div class="lg:col-span-5">{top_form(S, place)}</div></div></section>"""

MAP_CSS = '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css">'
LEAFLET_JS = '<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js" defer></script>'

def map_section(S, heading="Where we work", sub=None):
    pts = [{"n": x["name"], "lat": x["lat"], "lon": x["lon"], "u": S.city_path(x)} for x in S.cities]
    sub = sub or "Service areas and recent completed jobs. Tap a pin to see the job."
    return f"""<section class="py-16"><div class="max-w-6xl mx-auto px-5"><h2 class="display text-3xl font-extrabold mb-2">{heading}</h2><p class="text-bone/60 mb-6">{sub}</p>
<div id="jjMap" class="relative w-full h-[26rem] rounded-3xl border border-line overflow-hidden" data-cities='{json.dumps(pts)}' role="region" aria-label="Map of our service area and completed jobs"></div></div>{LEAFLET_JS}</section>"""

def seed_json(S):
    return '<script type="application/json" id="seedJobs">' + json.dumps([{**j, "id": "s" + str(i)} for i, j in enumerate(S.jobs)]).replace("</", "<\\/") + "</script>"

def reviews_section(S):
    static = ""
    if S.reviews:
        cards = "".join(f'<blockquote class="rounded-3xl bg-ink border border-line p-6"><div class="text-ember mb-2">{"★"*int(r.get("rating",5))}</div><p class="text-bone/80 mb-4">{r["text"]}</p><footer class="text-sm text-bone/50">— {r["author"]}{(", "+r["area"]) if r.get("area") else ""}</footer></blockquote>' for r in S.reviews[:6])
        static = f'<div id="staticReviews" class="grid md:grid-cols-3 gap-4">{cards}</div>'
    hid = "" if S.reviews else "hidden"
    return f"""<section class="py-16 bg-slate2 border-y border-line {hid}" id="reviewsLive"><div class="max-w-6xl mx-auto px-5"><div class="flex flex-wrap items-end justify-between gap-3 mb-8"><h2 class="display text-3xl font-extrabold">What customers say</h2><div class="text-sm text-bone/70" data-head>Reviews from Google</div></div>{static}<div class="grid md:grid-cols-3 gap-4" data-grid></div><a data-link target="_blank" rel="noopener" class="inline-block mt-6 text-sm text-ember font-semibold" href="#">Read all reviews on Google</a></div></section>"""

def home_jobs(S):
    return """<section id="homeJobs" class="hidden py-16"><div class="max-w-6xl mx-auto px-5"><div class="flex items-end justify-between mb-8"><h2 class="display text-3xl font-extrabold">Recent jobs</h2><a href="/our-work/" class="text-sm text-ember font-semibold">See all our work</a></div><div class="grid md:grid-cols-3 gap-4" data-grid></div></div></section>"""

def pricing_section(S):
    tiers = [{"price": "$250", "pct": "25%", "label": "a few large items, like a couch and a chair"},
             {"price": "$475", "pct": "50%", "label": "a room of furniture or a garage corner"},
             {"price": "$675", "pct": "75%", "label": "most of a garage or a big cleanout"},
             {"price": "$850", "pct": "100%", "label": "a full trailer: whole-room or yard cleanup"}]
    c = S.c
    return f"""<section id="pricing" class="py-20 bg-slate2 border-y border-line"><div class="max-w-7xl mx-auto px-5 grid lg:grid-cols-2 gap-14 items-center"><div>
<p class="text-xs font-semibold tracking-widest uppercase text-ember mb-4">Easy trailer pricing</p><h2 class="display text-4xl md:text-5xl font-extrabold leading-tight mb-5">You pay for the space you use.</h2>
<p class="text-bone/60 text-lg mb-7">Pricing is based on how much room your stuff takes up in our 16-ft trailer. Small pickups start around $99. Send a few pictures for an exact quote.</p>
<label for="loadSlider" class="block text-sm font-semibold mb-3">How full will the trailer be?</label>
<input id="loadSlider" type="range" min="1" max="4" value="2" step="1" class="w-full accent-ember" data-tiers='{json.dumps(tiers)}'>
<div class="flex justify-between text-xs text-bone/50 mt-2"><span>¼ load</span><span>½ load</span><span>¾ load</span><span>Full</span></div>
<div class="mt-7 flex flex-wrap items-baseline gap-3"><span class="text-bone/60 text-sm">Estimated</span><span id="loadPrice" class="display text-5xl font-extrabold text-ember">$475</span><span id="loadLabel" class="text-bone/60 text-sm"></span></div>
<p class="text-xs text-bone/40 mt-4">Ballpark only. Heavy materials (concrete, dirt, shingles) are priced separately. 10% off for seniors, veterans and first responders.</p>
<div class="mt-7 flex flex-wrap gap-3"><a href="#quote" class="rounded-full bg-ember hover:bg-emberDark text-ink font-bold px-8 py-4 transition">Get an exact quote</a><a href="sms:{c['phone_tel']}" class="rounded-full border border-bone/25 hover:border-bone/60 font-semibold px-8 py-4 transition">Text pictures</a></div></div>
<div class="flex justify-center"><div class="relative w-full max-w-md aspect-[4/3] rounded-3xl border border-line bg-ink overflow-hidden"><div class="absolute bottom-0 inset-x-0 bg-ember/20 border-t border-ember truck-fill" id="truckFill" style="height:50%"></div>
<div class="absolute inset-0 flex flex-col items-center justify-center text-center p-8"><div class="display text-7xl font-extrabold" id="truckPct">50%</div><div class="text-bone/60 text-sm mt-2">of our 16-ft trailer</div></div><div class="absolute top-4 left-4 text-xs tracking-widest uppercase text-bone/40">Load estimator</div></div></div></div></section>"""

def reel_html(S):
    if not S.reel: return ""
    imgs = "".join(f'<img src="{u}" alt="" loading="{"eager" if i == 0 else "lazy"}" class="reel-img{" on" if i == 0 else ""}">' for i, u in enumerate(S.reel))
    return f'<div id="heroReel" class="absolute inset-0" aria-hidden="true">{imgs}</div>'

def find_us(S):
    if not S.is_hq: return ""
    c = S.c; q = f"{c['street']}, {c['street_city']}, TX {c['zip']}".replace(" ", "+")
    return f"""<section id="visit" class="py-16 bg-slate2 border-y border-line"><div class="max-w-6xl mx-auto px-5 grid lg:grid-cols-2 gap-10 items-center"><div><p class="text-xs font-semibold tracking-widest uppercase text-ember mb-4">Find us</p><h2 class="display text-3xl md:text-4xl font-extrabold leading-tight mb-4">Based in Spring, TX.</h2>
<address class="not-italic text-lg text-bone/80 mb-4">{c['street']}<br>{c['street_city']}, TX {c['zip']}</address><p class="text-bone/60 mb-6">Call or text first to schedule a pickup. We come to you across the Spring, Klein, The Woodlands and Humble area.</p>
<div class="flex flex-wrap gap-3"><a href="tel:{c['phone_tel']}" class="rounded-full bg-ember hover:bg-emberDark text-ink font-bold px-6 py-3 transition">Call {c['phone_display']}</a><a rel="noopener" target="_blank" href="https://www.google.com/maps/dir/?api=1&destination={q}" class="rounded-full border border-bone/25 hover:border-bone/60 font-semibold px-6 py-3 transition">Get directions</a></div></div>
<iframe src="https://www.google.com/maps?q={q}&output=embed" title="Map showing {c['name']} location in Spring, TX" loading="lazy" referrerpolicy="no-referrer-when-downgrade" class="w-full h-80 lg:h-96 rounded-3xl border border-line" style="filter:invert(.92) hue-rotate(180deg) saturate(.8)"></iframe></div></section>"""

def work_page(S):
    c = S.c; hub = S.hub["name"]; path = "/our-work/"
    title = f"Our Work | Completed Junk Removal Jobs in {hub}, TX | {c['name']}"
    desc = f"See recent completed junk removal jobs around {hub}, TX: before and after photos, locations and what we hauled."
    schema = ld(business_schema(S), crumbs(S, [("Home", "/"), ("Our Work", path)]))
    pts = [{"n": x["name"], "lat": x["lat"], "lon": x["lon"], "u": S.city_path(x)} for x in S.cities]
    body = f"""<main><section class="pt-28 pb-12 md:pt-36 md:pb-16 border-b border-line" style="background:radial-gradient(circle at 70% 30%,rgba(20,245,0,.14),transparent 60%),#06120F"><div class="max-w-6xl mx-auto px-5">{crumb_html([("Home","/"),("Our Work",path)])}<h1 class="display text-5xl sm:text-6xl lg:text-7xl font-extrabold leading-[0.98] mb-4">See Our Work</h1><p class="text-lg text-bone/70 max-w-2xl">Real jobs from our crew around {", ".join(x["name"] for x in S.cities)}. Every pin on the map is a completed job.</p><p class="mt-4 text-sm text-ember font-semibold" id="jobCount"></p></div></section>
<section class="py-10"><div class="max-w-6xl mx-auto px-5"><div id="jjMap" class="relative w-full h-[28rem] md:h-[32rem] rounded-3xl border border-line overflow-hidden" data-cities='{json.dumps(pts)}' role="region" aria-label="Map of completed jobs"></div></div>{LEAFLET_JS}</section>
<section class="pb-20"><div class="max-w-6xl mx-auto px-5 grid lg:grid-cols-3 gap-8 items-start">
<div class="lg:col-span-2"><div id="jobGrid" class="grid sm:grid-cols-2 gap-5"></div><div class="text-center mt-8"><button id="loadMore" type="button" class="hidden rounded-full bg-ember hover:bg-emberDark text-ink font-bold px-8 py-4 transition">Show all jobs</button></div></div>
<aside class="lg:sticky lg:top-24 rounded-3xl border border-line bg-slate2 p-5" aria-label="Recent jobs"><h2 class="display text-xl font-extrabold mb-3">Recent jobs</h2><div id="jobSide" class="space-y-1"></div><a href="#quote" class="mt-4 block text-center rounded-full bg-ember hover:bg-emberDark text-ink font-bold px-6 py-3 transition">Get a free quote</a></aside></div></section>
{reviews_section(S)}{quote_form(S, hub + ", TX", "quote")}{seed_json(S)}</main>"""
    S.write(path, head(S, title, desc, path, schema, MAP_CSS) + header(S) + body + footer(S))

def crew_page(S):
    c = S.c; path = "/crew/"
    pts = [{"n": ct[0], "lat": ct[1], "lon": ct[2]} for r in ROUTES.values() for ct in r["cities"]]
    inp = "bg-ink border border-line rounded-xl px-4 py-3 w-full focus:outline-none focus:border-ember"
    city_opts = "".join(f'<optgroup label="{r["name"]}">' + "".join(f"<option>{ct[0]}</option>" for ct in r["cities"]) + "</optgroup>" for r in ROUTES.values())
    svc_opts = "".join(f"<option>{o}</option>" for o in HOME_SERVICES)
    body = f"""<main class="pt-24 pb-24"><div class="max-w-xl mx-auto px-5"><h1 class="display text-3xl font-extrabold mb-2">Crew job photos</h1><p class="text-bone/60 mb-6">Crew only. Take a before photo when you start, then the after photo when you finish. The job drops onto the right website's map and Google profile automatically.</p>
<div id="crewApp" data-cities='{json.dumps(pts)}'>
<form id="crewLogin" class="grid gap-3 mb-8"><input name="pin" type="text" autocapitalize="characters" autocomplete="off" placeholder="Your crew code" required class="{inp}"><button class="rounded-full bg-ember hover:bg-emberDark text-ink font-bold px-8 py-4 transition">Sign in</button></form>
<div id="crewMain" hidden>
<p id="crewHi" class="text-bone/70 mb-6"></p>
<h2 class="display text-xl font-extrabold mb-3">Open jobs <span class="text-bone/40 text-sm font-normal">(waiting on the after photo)</span></h2>
<div id="crewOpen" class="grid gap-3 mb-10"></div>
<h2 class="display text-xl font-extrabold mb-3">Start a new job</h2>
<form id="crewForm" class="grid gap-4">
<select name="service" required class="{inp}"><option value="">What are you hauling?</option>{svc_opts}</select>
<button type="button" id="gpsBtn" class="rounded-xl border border-line px-4 py-3 text-left">📍 Use my location (recommended)</button>
<select name="city" class="{inp}"><option value="">...or pick the city</option>{city_opts}</select>
<input name="area" placeholder="Neighborhood (optional, no street addresses)" class="{inp}">
<label class="block"><span class="text-sm text-bone/70">Before photo (required)</span><input name="before" type="file" accept="image/*" capture="environment" required class="mt-1 block w-full text-sm"></label>
<label class="block"><span class="text-sm text-bone/50">Already done? Add the after photo now (optional)</span><input name="after" type="file" accept="image/*" capture="environment" class="mt-1 block w-full text-sm"></label>
<textarea name="description" rows="2" maxlength="600" placeholder="1-3 sentences about the job (optional)" class="{inp}"></textarea>
<label class="flex items-center gap-3 text-sm text-bone/70"><input type="checkbox" name="gbp" checked class="accent-ember w-5 h-5"> Also post to our Google Business Profile</label>
<button id="crewBtn" class="rounded-full bg-ember hover:bg-emberDark text-ink font-bold px-8 py-4 transition">Start job</button></form>
</div>
<p id="crewMsg" class="text-sm text-bone/70 mt-4" role="status"></p></div><p class="text-xs text-bone/40 mt-6">Do not include customer faces, house numbers, license plates or street addresses. Photos are posted publicly. Map pins are shown only to about 1 km.</p></div></main>"""
    S.write(path, head(S, f"Crew upload | {c['name']}", "Crew upload", path, "", '<meta name="robots" content="noindex, nofollow">').replace('<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">', "") + header(S) + body + footer(S).replace("/assets/form.js", "/assets/crew.js"))

def admin_page(S):
    path = "/admin/"
    names = {k: {"name": v["name"], "domain": (json.loads((ROOT / "sites" / f"{k}.json").read_text())["domain"] if (ROOT / "sites" / f"{k}.json").exists() else "junkjunkiesindiana.com")} for k, v in ROUTES.items()}
    body = f"""<main class="pt-28 pb-24"><div class="max-w-6xl mx-auto px-5"><h1 class="display text-4xl font-extrabold mb-2">Owner dashboard</h1><p class="text-bone/60 mb-8">All sites in one place: jobs, Google posting status and quick controls. Needs the admin PIN.</p><div id="adminApp" data-sites='{json.dumps(names)}'></div></div></main>"""
    S.write(path, head(S, "Dashboard", "Owner dashboard", path, "", '<meta name="robots" content="noindex, nofollow">').replace('<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">', "") + header(S) + body + footer(S).replace("/assets/form.js", "/assets/admin.js"))

def crm_page(S):
    path = "/crm/"
    body = f"""<main class="pt-28 pb-24"><div class="max-w-7xl mx-auto px-5"><div class="flex flex-wrap items-end justify-between gap-3 mb-6"><div><h1 class="display text-4xl font-extrabold mb-1">Customer CRM</h1><p class="text-bone/60">Every quote request from all six sites, worked as a pipeline. Needs the admin PIN.</p></div><a href="/admin/" class="text-sm text-ember underline">Back to dashboard</a></div><div id="crmApp"></div></div></main>"""
    S.write(path, head(S, "CRM", "Owner CRM", path, "", '<meta name="robots" content="noindex, nofollow">').replace('<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">', "") + header(S) + body + footer(S).replace("/assets/form.js", "/assets/crm.js"))

def home(S):
    c = S.c; hub = S.hub["name"]; names = [x["name"] for x in S.cities]
    others = ", ".join(names[1:-1]) + (" and " + names[-1] if len(names) > 1 else "")
    faq = [(f"Do you offer junk removal in {hub}, TX?", f"Yes. We serve {hub} and nearby {others}. Call {c['phone_display']} for a quote."),
           ("How do I get a quote?", f"Use the form, call or text photos to {c['phone_display']}. We give a firm price before we start."),
           ("What can't you take?", "Hazardous materials such as paint, chemicals, asbestos and fuel."),
           ("Do you offer discounts?", "Yes, we offer a veteran and first responder discount. Mention it when you call."),
           ("What do you haul?", "21 services in all: junk removal, cleanouts, furniture and appliances, and debris removal for construction, yard, storm, roofing, remodeling, demolition and brush.")]
    title = f"Junk Removal {hub}, TX | Debris, Hoarder & Appliance Removal | {c['name']}"
    desc = f"Junk removal in {hub}, TX and {others}. Debris removal, cleanouts, appliance and furniture removal. Veteran and first responder discount. Call {c['phone_display']}."
    schema = ld(business_schema(S), {"@context": "https://schema.org", "@type": "WebSite", "name": c["name"], "url": S.base + "/", "publisher": {"@id": S.biz_id}}, faq_schema(faq))
    svc = "".join(f'<a href="{S.svc_path(s)}" class="rounded-2xl bg-slate2 border border-line p-6 hover:border-ember/60 transition"><div class="display text-ember font-extrabold mb-2">{s["icon"]}</div><h3 class="display font-bold text-lg mb-1">{s["name"]}</h3><p class="text-sm text-bone/60">{s["blurb"]}</p></a>' for s in SERVICES)
    areas = "".join(f'<a href="{S.city_path(x)}" class="rounded-2xl border border-line bg-ink p-5 hover:border-ember/60 transition"><div class="font-semibold">{x["name"]}</div><div class="text-xs text-bone/50 mt-1">{x["county"]} County</div></a>' for x in S.cities)
    body = f'''<main><section class="relative flex items-center pt-20 pb-10 md:pt-28 md:pb-20 overflow-hidden"><img src="/assets/hero.webp" width="1280" height="720" alt="" class="absolute inset-0 w-full h-full object-cover opacity-55" fetchpriority="high">{reel_html(S)}<div class="absolute inset-0 bg-gradient-to-t from-ink via-ink/70 to-ink/10"></div>
<div class="relative max-w-7xl mx-auto px-5 w-full grid lg:grid-cols-12 gap-8 lg:gap-10 items-center"><div class="lg:col-span-7">
<p class="inline-flex items-center gap-2 text-[11px] sm:text-xs font-semibold tracking-widest uppercase text-ember mb-3 sm:mb-6"><span class="w-2 h-2 rounded-full bg-ember animate-pulse"></span> Serving {", ".join(names)}</p>
<div class="hidden sm:block mb-5"><div class="logo-shine"><img src="/assets/logo.png" width="120" height="120" alt="{c['name']} logo" class="w-28 h-28"></div></div>
<h1 class="display text-[34px] sm:text-6xl lg:text-7xl font-extrabold leading-[0.98] mb-3 sm:mb-5">Junk Removal in <span class="text-ember">{hub}, TX</span></h1>
<div class="rig relative max-w-xl mb-3 sm:mb-6 rounded-xl overflow-hidden border border-line" style="aspect-ratio:1100/300"><img src="/assets/rig1.webp" width="1100" height="300" alt="{c['name']} truck and trailer" class="absolute inset-0 w-full h-full object-contain bg-black"><img src="/assets/rig2.webp" width="1100" height="300" alt="" loading="lazy" class="rig2 absolute inset-0 w-full h-full object-contain bg-black"></div>
<p class="hidden sm:block text-base md:text-xl text-bone/75 max-w-xl mb-6">Reliable junk removal, debris cleanup, cleanouts, appliance and furniture removal. {S.hub["note"]}</p>
<div class="hidden sm:flex gap-3"><a href="tel:{c['phone_tel']}" class="inline-flex justify-center rounded-full border border-bone/25 hover:border-bone/60 font-semibold px-8 py-4 transition">Call {c['phone_display']}</a></div></div>
<div class="lg:col-span-5">{top_form(S, hub + ", TX")}</div></section>
<section id="services" class="py-24"><div class="max-w-7xl mx-auto px-5"><p class="text-xs font-semibold tracking-widest uppercase text-ember mb-4">What we do</p><h2 class="display text-4xl md:text-5xl font-extrabold leading-tight mb-6 max-w-3xl">If it needs to go, we haul it.</h2><p class="text-bone/60 text-lg max-w-2xl mb-12">{S.hub["housing"]}</p><div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">{svc}</div></div></section>
{pricing_section(S)}
{home_jobs(S)}
{reviews_section(S)}
{map_section(S)}
{find_us(S)}
<section id="areas" class="py-16 bg-slate2 border-y border-line"><div class="max-w-6xl mx-auto px-5"><h2 class="display text-3xl font-extrabold mb-3">Service areas</h2><p class="text-bone/60 mb-8">{S.hub["name"]} is our home base. We also serve {others}.</p><div class="grid grid-cols-2 md:grid-cols-4 gap-3">{areas}</div></div></section>
{quote_form(S, hub + ", TX")}
<section id="faq" class="py-20"><div class="max-w-4xl mx-auto px-5"><h2 class="display text-3xl md:text-4xl font-extrabold mb-8">Questions we get every day.</h2>{faq_html(faq)}</div></section></main>'''
    S.write("/", head(S, title, desc, "/", schema, MAP_CSS + '<link rel="preload" as="image" href="/assets/hero.webp" fetchpriority="high">') + header(S) + body + footer(S))

def city_page(S, key):
    x = CITIES[key]; c = S.c; path = S.city_path(x); n = x["name"]
    near = [y for y in S.cities if y is not x]
    title = f"Junk Removal {n}, TX | Same-Day Hauling & Cleanouts | {c['name']}"
    desc = f"Junk removal in {n}, Texas ({x['county']} County). Furniture, appliances, debris and cleanouts with upfront pricing. Call {c['phone_display']}."
    faq = [(f"How do I get a junk removal quote in {n}?", f"Text photos to {c['phone_display']}, call, or use the form. We give a firm price before we start."),
           (f"What do you haul in {n}?", f"{x['jobs'].capitalize()}, plus everything else on our service list."),
           ("Do you offer a veteran or first responder discount?", "Yes. Mention it when you call or in the form."),
           ("What can't you take?", "Hazardous materials such as paint, chemicals, asbestos and fuel.")]
    schema = ld(business_schema(S), {"@context": "https://schema.org", "@type": "Service", "name": f"Junk Removal in {n}, TX", "serviceType": "Junk removal", "provider": {"@id": S.biz_id}, "areaServed": {"@type": "City", "name": f"{n}, TX", "geo": {"@type": "GeoCoordinates", "latitude": x["lat"], "longitude": x["lon"]}}, "url": S.base + path}, crumbs(S, [("Home", "/"), ("Service Areas", "/areas/"), (n, path)]), faq_schema(faq))
    pills = "".join(f'<li class="rounded-full border border-line bg-slate2 px-4 py-2 text-sm">{a}</li>' for a in x["areas"])
    cards = "".join(f'<a href="{S.svc_path(s)}" class="rounded-2xl bg-slate2 border border-line p-6 hover:border-ember/60 transition"><div class="display text-ember font-extrabold mb-2">{s["icon"]}</div><h3 class="display font-bold text-lg mb-1">{s["name"]}</h3><p class="text-sm text-bone/60">{s["blurb"]}</p></a>' for s in SERVICES[:6])
    nl = "".join(f'<a href="{S.city_path(y)}" class="rounded-2xl border border-line bg-ink p-4 hover:border-ember/60 transition"><div class="font-semibold">{y["name"]}</div><div class="text-xs text-bone/50">{y["county"]} County</div></a>' for y in near)
    body = f'''<main>{hero_small(S, f"Junk Removal in {n}, Texas", f"Furniture, appliances, debris and cleanouts hauled away in {n} and across {x['county']} County.", crumb_html([("Home","/"),("Service Areas","/areas/"),(n,path)]))}
<section class="py-16"><div class="max-w-5xl mx-auto px-5 prose-j"><h2>{n}'s junk removal crew</h2><p>{x['housing']}</p><p>In {n} we most often handle {x['jobs']}. {x['note']}</p>
<p>Send photos or a description, get a firm price, pick a time, and we load everything up. Zip codes we regularly serve in {n} include {x['zips']}.</p>
<h2>Neighborhoods and areas in {n}</h2><ul class="flex flex-wrap gap-2 mb-6 not-prose">{pills}</ul><p>Do not see your street? Call {c['phone_display']}. If you are in or near {n}, we likely cover you.</p></div></section>
<section class="py-16 bg-slate2 border-y border-line"><div class="max-w-5xl mx-auto px-5"><h2 class="display text-3xl font-extrabold mb-8">What we haul in {n}</h2><div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">{cards}</div></div></section>
{quote_form(S, n + ", TX")}<section class="py-16"><div class="max-w-4xl mx-auto px-5"><h2 class="display text-3xl font-extrabold mb-8">{n} junk removal FAQ</h2>{faq_html(faq)}</div></section>
<section class="py-16 bg-slate2 border-t border-line"><div class="max-w-5xl mx-auto px-5"><h2 class="display text-2xl font-extrabold mb-6">Nearby areas we serve</h2><div class="grid grid-cols-2 md:grid-cols-3 gap-3">{nl}</div></div></section></main>'''
    S.write(path, head(S, title, desc, path, schema, '<link rel="preload" as="image" href="/assets/hero.webp" fetchpriority="high">') + header(S) + body + footer(S))

def service_page(S, s):
    c = S.c; hub = S.hub; path = S.svc_path(s)
    title = f"{s['name']} {hub['name']}, TX | {c['name']}"
    desc = f"{s['name']} in {hub['name']} and {', '.join(x['name'] for x in S.cities[1:])}, Texas. {s['blurb']} Call {c['phone_display']}."
    schema = ld(business_schema(S), {"@context": "https://schema.org", "@type": "Service", "name": f"{s['name']} in {hub['name']}, TX", "serviceType": s["name"], "provider": {"@id": S.biz_id}, "areaServed": [{"@type": "City", "name": x["name"] + ", TX"} for x in S.cities], "url": S.base + path}, crumbs(S, [("Home", "/"), ("Services", "/services/"), (s["name"], path)]), faq_schema(s["faq"]))
    items = "".join(f'<li class="flex gap-3"><span class="text-ember">✓</span><span>{i}</span></li>' for i in s["items"])
    cities = "".join(f'<a href="{S.city_path(x)}" class="rounded-2xl border border-line bg-ink p-4 hover:border-ember/60 transition"><div class="font-semibold">{x["name"]}</div></a>' for x in S.cities)
    others = "".join(f'<a href="{S.svc_path(o)}" class="rounded-2xl border border-line bg-ink p-4 hover:border-ember/60 transition"><div class="font-semibold">{o["name"]}</div></a>' for o in SERVICES if o is not s)
    body = f'''<main>{hero_small(S, f"{s['name']} in {hub['name']}, TX", s['blurb'], crumb_html([("Home","/"),("Services","/services/"),(s['name'],path)]))}
<section class="py-16"><div class="max-w-5xl mx-auto px-5 prose-j"><h2>{s['name']} in {hub['name']}</h2><p>{s['intro']}</p><p>{hub['housing']} {s['name']} jobs here often come alongside {hub['jobs']}.</p>
<h2>What this covers</h2><ul class="grid sm:grid-cols-2 gap-3 text-bone/80 mb-6 not-prose">{items}</ul>
<h2>How it works</h2><p><strong>1. Send photos or details.</strong> <strong>2. Get a firm price.</strong> <strong>3. We take care of it.</strong> Veteran and first responder discount available.</p></div></section>
{quote_form(S, hub['name'] + ", TX")}<section class="py-16"><div class="max-w-4xl mx-auto px-5"><h2 class="display text-3xl font-extrabold mb-8">{s['name']} FAQ</h2>{faq_html(s['faq'])}</div></section>
<section class="py-16 bg-slate2 border-t border-line"><div class="max-w-5xl mx-auto px-5"><h2 class="display text-2xl font-extrabold mb-6">Where we offer {s['name'].lower()}</h2><div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-10">{cities}</div><h2 class="display text-2xl font-extrabold mb-6">Other services</h2><div class="grid grid-cols-2 md:grid-cols-4 gap-3">{others}</div></div></section></main>'''
    S.write(path, head(S, title, desc, path, schema) + header(S) + body + footer(S))

def hub_page(S, path, title, desc, h1, sub, cards, crumb, extra_body="", extra_head=""):
    schema = ld(business_schema(S), crumbs(S, [("Home", "/"), (crumb, path)]))
    body = f'<main>{hero_small(S, h1, sub, crumb_html([("Home","/"),(crumb,path)]))}<section class="py-16"><div class="max-w-6xl mx-auto px-5 grid sm:grid-cols-2 lg:grid-cols-3 gap-4">{cards}</div></section>{extra_body}{quote_form(S, S.hub["name"] + ", TX")}</main>'
    S.write(path, head(S, title, desc, path, schema, extra_head) + header(S) + body + footer(S))

def build_site(S):
    c = S.c; hub = S.hub["name"]
    if S.out.exists(): shutil.rmtree(S.out)
    (S.out / "assets").mkdir(parents=True)
    # assets
    shutil.copy(ROOT / "shared" / "hero.webp", S.out / "assets/hero.webp")
    for rg in ("rig1.webp", "rig2.webp"): shutil.copy(ROOT / "shared" / "rig" / rg, S.out / "assets" / rg)
    for f in ["form.js", "app.js", "crew.js", "admin.js", "crm.js"]: shutil.copy(ROOT / "shared" / f, S.out / "assets" / f)
    shutil.copytree(ROOT / "shared" / "api", S.out / "api"); shutil.copy(S.out / "api" / "package.json", S.out / "package.json"); (S.out / "api" / "package.json").unlink()
    (S.out / "api" / "_site.js").write_text(f'export default {json.dumps(S.slug)};\n')
    (S.out / "api" / "_routes.js").write_text(ROUTES_JS)
    rd = ROOT / "data" / S.slug / "reel"
    if rd.exists(): shutil.copytree(rd, S.out / "assets/reel")
    from PIL import Image
    logo = Image.open(ROOT / "assets/logos" / c["logo"]).convert("RGB")
    import numpy as np
    a = np.asarray(logo.resize((900, 900), Image.LANCZOS)).astype(float)
    Image.fromarray(np.dstack([a, np.clip(a.max(axis=2) * 3.0, 0, 255)]).astype("uint8"), "RGBA").save(S.out / "assets/logo.png", optimize=True)
    w, h = logo.size; head_img = logo.crop((int(w*.19), int(h*.05), int(w*.81), int(h*.49)))
    side = int(max(head_img.size) * 1.28); sq = Image.new("RGB", (side, side), (0, 0, 0)); sq.paste(head_img, ((sq.size[0]-head_img.size[0])//2, (sq.size[1]-head_img.size[1])//2))
    sq.resize((256, 256)).save(S.out / "assets/logo-icon.png", optimize=True); sq.resize((64, 64)).save(S.out / "favicon.png"); sq.resize((192, 192), Image.LANCZOS).save(S.out / "favicon-192.png", optimize=True); sq.resize((256, 256), Image.LANCZOS).save(S.out / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    logo.resize((336, 336), Image.LANCZOS).save(S.out / "assets/logo-badge.png", optimize=True)  # the full location logo, city name and phone included, for the header
    from PIL import ImageEnhance
    bg = Image.open(ROOT / "shared/hero.webp").convert("RGB").resize((1200, 675)).crop((0, 22, 1200, 652)); bg = ImageEnhance.Brightness(bg).enhance(.5).convert("RGBA")
    lg = logo.convert("RGBA").resize((520, 520)); bg.alpha_composite(lg, (340, 55)); bg.convert("RGB").save(S.out / "assets/og-image.jpg", quality=85, optimize=True)
    for j in S.jobs:  # copy job photos
        pass
    src_jobs = ROOT / "data" / S.slug / "photos"
    if src_jobs.exists(): shutil.copytree(src_jobs, S.out / "assets/jobs")
    # pages
    home(S)
    for k in c["cities"]: city_page(S, k)
    for s in SERVICES: service_page(S, s)
    cc = "".join(f'<a href="{S.city_path(x)}" class="rounded-2xl bg-slate2 border border-line p-6 hover:border-ember/60 transition"><h2 class="display font-bold text-xl mb-1">Junk Removal in {x["name"]}</h2><p class="text-sm text-bone/60">{x["county"]} County · {x["zips"]}</p></a>' for x in S.cities)
    hub_page(S, "/areas/", f"Junk Removal Service Areas | {hub} & Nearby, TX | {c['name']}", f"We serve {', '.join(x['name'] for x in S.cities)}, Texas. Call {c['phone_display']}.", "Junk Removal Service Areas", f"Serving {', '.join(x['name'] for x in S.cities)}, Texas.", cc, "Service Areas", map_section(S), MAP_CSS)
    sc = "".join(f'<a href="{S.svc_path(s)}" class="rounded-2xl bg-slate2 border border-line p-6 hover:border-ember/60 transition"><div class="display text-ember font-extrabold mb-2">{s["icon"]}</div><h2 class="display font-bold text-xl mb-1">{s["name"]}</h2><p class="text-sm text-bone/60">{s["blurb"]}</p></a>' for s in SERVICES)
    hub_page(S, "/services/", f"Junk Removal Services {hub}, TX | {c['name']}", f"Junk removal, debris removal, cleanouts, appliance removal and more in {hub}, TX. Call {c['phone_display']}.", "Our Services", "From a single couch to a whole-property cleanout.", sc, "Services")
    work_page(S); crew_page(S); admin_page(S); crm_page(S)
    # site files
    urls = [("/", "1.0"), ("/areas/", "0.8"), ("/services/", "0.8"), ("/our-work/", "0.6")] + [(S.svc_path(s), "0.8") for s in SERVICES] + [(S.city_path(x), "0.9" if x is S.hub else "0.7") for x in S.cities]
    (S.out / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"<url><loc>{S.base}{u}</loc><lastmod>{TODAY}</lastmod><changefreq>weekly</changefreq><priority>{p}</priority></url>\n" for u, p in urls) + "</urlset>\n")
    (S.out / "robots.txt").write_text(f"User-agent: *\nAllow: /\nDisallow: /crew/\nDisallow: /api/\nDisallow: /admin/\n\nSitemap: {S.base}/sitemap.xml\n")
    (S.out / "site.webmanifest").write_text(json.dumps({"name": c["name"], "short_name": "Junk Junkies", "start_url": "/", "display": "standalone", "background_color": "#0B0D10", "theme_color": "#14F500", "icons": [{"src": "/assets/logo-icon.png?v=2", "sizes": "256x256", "type": "image/png"}]}))
    (S.out / "llms.txt").write_text(f"# {c['name']}\n\n> Junk removal, debris removal, cleanouts, appliance removal and more in {', '.join(x['name'] for x in S.cities)}, Texas. Phone/text: {c['phone_display']}.\n\n## Services\n" + "".join(f"- [{s['name']}]({S.base}{S.svc_path(s)}): {s['blurb']}\n" for s in SERVICES) + "\n## Areas\n" + "".join(f"- [{x['name']}, TX]({S.base}{S.city_path(x)})\n" for x in S.cities))
    (S.out / "vercel.json").write_text(json.dumps({"redirects": [{"source": x, "destination": "/crm/", "permanent": False} for x in ["/CRM", "/CRM/"]], "cleanUrls": True, "trailingSlash": True, "functions": {"api/*.js": {"maxDuration": 20}}, "crons": [{"path": "/api/gbp-sync", "schedule": "0 13 * * *"}], "headers": [{"source": "/assets/(.*)", "headers": [{"key": "Cache-Control", "value": "public, max-age=86400, stale-while-revalidate=604800"}]}, {"source": "/(.*)", "headers": [{"key": "X-Content-Type-Options", "value": "nosniff"}, {"key": "Referrer-Policy", "value": "strict-origin-when-cross-origin"}, {"key": "X-Frame-Options", "value": "SAMEORIGIN"}]}]}, indent=2))
    (S.out / "404.html").write_text(head(S, f"Page not found | {c['name']}", "Page not found.", "/404", "", '<meta name="robots" content="noindex">').replace('<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">', "") + header(S) + f'<main class="min-h-[70vh] grid place-items-center text-center px-5 pt-24"><div><h1 class="display text-5xl font-extrabold mb-4">Page not found.</h1><p class="text-bone/60 mb-6">But we can still haul your junk.</p><a href="/" class="rounded-full bg-ember text-ink font-bold px-8 py-4">Back to home</a></div></main>' + footer(S))
    print(f"{S.slug}: {len(urls)} pages -> dist/{S.slug}")

if __name__ == "__main__":
    for k in (sys.argv[1:] or SITES): build_site(Site(SITES[k]))
