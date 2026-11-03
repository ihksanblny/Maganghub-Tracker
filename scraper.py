import os
import sys
import re
import json
import csv
import time
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from bumn_classifier import classify_company

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)
JSON_OUTPUT = os.path.join(DATA_DIR, "bumn_maganghub.json")
CSV_OUTPUT = os.path.join(DATA_DIR, "bumn_maganghub.csv")

BUMN_TARGET_KEYWORDS = [
    # Status / Umum
    "persero", "perum", "bumn",
    
    # Perbankan & Jasa Keuangan
    "mandiri", "bank mandiri", "bank bri", "bank rakyat indonesia",
    "bank bni", "bank negara indonesia", "bank btn", "bank tabungan negara",
    "bsi", "bank syariah indonesia", "pegadaian", "pnm", "permodalan nasional madani",
    "danareksa", "jasa raharja", "jasindo", "asei indonesia", "taspen", "asabri",
    "jamkrindo", "askrindo", "ifg",
    
    # Energi, Migas & Tambang
    "pertamina", "pln", "perusahaan listrik negara", "indonesia power", "nusantara power",
    "mind id", "bukit asam", "aneka tambang", "antam", "timah", "inalum", "pgn",
    "elnusa", "pertamina hulu energi", "pertamina patra niaga",
    
    # Infrastruktur, Karya, Semen & Baja
    "wijaya karya", "wika", "waskita karya", "adhi karya", "hutama karya", "pt pp",
    "pembangunan perumahan", "brantas abipraya", "nindya karya", "jasa marga",
    "semen indonesia", "semen padang", "semen gresik", "semen tonasa", "perumnas",
    "krakatau steel", "krakatau medika",
    
    # Transportasi, Logistik & Aviasi
    "kereta api indonesia", "kai", "kai bandara", "kai logistik", "kai wisata",
    "pelindo", "pelabuhan indonesia", "asdp indonesia ferry", "pelni",
    "garuda indonesia", "citilink", "gmf aeroasia", "angkasa pura",
    "damri", "pos indonesia", "pos logistik",
    
    # Telekomunikasi & Teknologi
    "telkom indonesia", "telkomsel", "metranet", "infomedia", "mitratel", "telkom akses",
    
    # Kesehatan & Farmasi
    "bio farma", "kimia farma", "indofarma", "pertamedika", "pelindo husada citra",
    
    # Pangan, Pertanian & Kehutanan
    "bulog", "pupuk indonesia", "petrokimia gresik", "pupuk kujang", "pupuk kaltim", "pusri",
    "perkebunan nusantara", "ptpn", "id food", "rajawali nusantara", "perhutani", "jasa tirta",
    
    # Manufaktur & Pertahanan
    "pindad", "dirgantara indonesia", "ptdi", "pal indonesia", "len industri", "dahana",
    "peruri", "sucofindo", "surveyor indonesia", "sarinah"
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

def fetch_single_page(keyword, page=1):
    params = [
        ("keyword", keyword),
        ("organizer_type[id]", "company"),
        ("organizer_type[label]", "Perusahaan"),
        ("page", str(page))
    ]
    url = f"https://maganghub.kemnaker.go.id/magang-nasional/penyelenggara?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
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
        return [], 1

def scrape_keyword_all_pages(keyword):
    items, last_page = fetch_single_page(keyword, 1)
    all_kw_items = list(items)
    
    # Fetch subsequent pages if any (limit to max 5 pages per keyword to keep it fast & relevant)
    max_p = min(last_page, 5)
    for p in range(2, max_p + 1):
        p_items, _ = fetch_single_page(keyword, p)
        all_kw_items.extend(p_items)
        time.sleep(0.1)
        
    return keyword, all_kw_items

def run_scraper(max_workers=5):
    print("=" * 65)
    print("🔍 MAGANGHUB BUMN SCRAPER (KEMNAKER RI)")
    print("=" * 65)
    print(f"Targeting {len(BUMN_TARGET_KEYWORDS)} BUMN keywords with {max_workers} concurrent workers...")
    
    t_start = time.time()
    raw_companies_map = {}
    completed_kw = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_kw = {executor.submit(scrape_keyword_all_pages, kw): kw for kw in BUMN_TARGET_KEYWORDS}
        for future in as_completed(future_to_kw):
            kw = future_to_kw[future]
            try:
                keyword, items = future.result()
                completed_kw += 1
                for it in items:
                    raw_companies_map[it["id"]] = it
                print(f"[{completed_kw:02d}/{len(BUMN_TARGET_KEYWORDS)}] '{keyword}': +{len(items)} items (Total unique so far: {len(raw_companies_map)})", flush=True)
            except Exception as e:
                print(f"Error scraping {kw}: {e}", flush=True)

    print(f"\n✅ Scraping selesai dalam {time.time() - t_start:.2f}s!")
    print(f"Total perusahaan mentah terkumpul: {len(raw_companies_map)}")
    
    print("\n🔬 Mengklasifikasikan data BUMN & menyaring false-positives...")
    bumn_list = []
    for comp_id, comp in raw_companies_map.items():
        classified = classify_company(comp)
        if classified:
            bumn_list.append(classified)
            
    # Sort by active vacancies descending, then by name
    bumn_list.sort(key=lambda x: (-x["vacancies"], x["name"]))
    
    # Save to JSON
    with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(bumn_list, f, ensure_ascii=False, indent=2)
    print(f"📁 JSON tersimpan: {JSON_OUTPUT}")
    
    # Save to CSV
    if bumn_list:
        fieldnames = ["name", "type", "cluster", "vacancies", "city", "address", "url", "description", "matched_keyword", "id", "logoUrl"]
        with open(CSV_OUTPUT, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in bumn_list:
                writer.writerow(row)
        print(f"📁 CSV tersimpan: {CSV_OUTPUT}")
        
    print("\n" + "=" * 65)
    print("📊 RINGKASAN DATA BUMN DI MAGANGHUB")
    print("=" * 65)
    total_vacancies = sum(b["vacancies"] for b in bumn_list)
    induk_count = sum(1 for b in bumn_list if "Induk" in b["type"])
    anak_count = sum(1 for b in bumn_list if "Anak" in b["type"])
    with_vacancies = sum(1 for b in bumn_list if b["vacancies"] > 0)
    
    print(f"Total Entitas BUMN Ditemukan : {len(bumn_list)}")
    print(f" - BUMN Induk (Persero/Perum): {induk_count}")
    print(f" - Anak / Cucu / Afiliasi   : {anak_count}")
    print(f"Total Lowongan Aktif BUMN   : {total_vacancies}")
    print(f"Perusahaan dgn Lowongan Aktif: {with_vacancies} / {len(bumn_list)}")
    
    # Cluster summary
    cluster_counts = {}
    for b in bumn_list:
        cluster_counts[b["cluster"]] = cluster_counts.get(b["cluster"], 0) + 1
    print("\nDistribusi Berdasarkan Sektor:")
    for cluster, count in sorted(cluster_counts.items(), key=lambda x: -x[1]):
        print(f" - {cluster:<35}: {count} perusahaan")
        
    print("\nTop 10 BUMN dengan Lowongan Aktif Terbanyak:")
    for i, b in enumerate(bumn_list[:10], 1):
        print(f" {i:2d}. {b['name']} ({b['city']}) -> {b['vacancies']} lowongan")
        
    return bumn_list

if __name__ == "__main__":
    run_scraper(max_workers=6)
