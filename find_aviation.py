import urllib.request
import urllib.parse
import re
import json

AVIATION_KEYWORDS = [
    "garuda", "citilink", "gmf", "aero", "aerofood", "gapura", "angkasa", "pura",
    "injourney", "airnav", "lppnpi", "penerbangan", "aviation", "dirgantara",
    "pelita air", "pelita", "merpati", "ias", "bandara", "navigasi"
]

def fetch_maganghub(keyword, page=1):
    params = [
        ("keyword", keyword),
        ("organizer_type[id]", "company"),
        ("organizer_type[label]", "Perusahaan"),
        ("page", str(page))
    ]
    url = f"https://maganghub.kemnaker.go.id/magang-nasional/penyelenggara?{urllib.parse.urlencode(params)}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            m = re.search(r'\\"initialData\\":\{(\\"data\\":\[.*?\]),\\"links\\":\{.*?\},\\"meta\\":(\{.*?\})\},\\"path\\"', html)
            if not m:
                return [], 1
            raw_data = m.group(1).encode('utf-8').decode('unicode_escape')
            raw_meta = m.group(2).encode('utf-8').decode('unicode_escape')
            items = json.loads("{" + raw_data + "}")["data"]
            meta = json.loads(raw_meta)
            return items, meta.get("lastPage", 1)
    except Exception as e:
        print(f"Error {keyword}: {e}")
        return [], 1

print("Searching aviation entities in Maganghub...")
found = {}
for kw in AVIATION_KEYWORDS:
    items, last_p = fetch_maganghub(kw, 1)
    for it in items:
        found[it["id"]] = it
    for p in range(2, min(last_p, 4) + 1):
        sub_items, _ = fetch_maganghub(kw, p)
        for it in sub_items:
            found[it["id"]] = it

print(f"\nTotal raw aviation-related items found: {len(found)}")
for it in found.values():
    print(f"- [{it.get('id')}] {it.get('name')} | Vacancies: {it.get('totalActiveVacancies')} | City: {it.get('city', {}).get('name') if it.get('city') else 'N/A'}")

