import re

BUMN_HOLDINGS = {
    "Perbankan & Jasa Keuangan": [
        "mandiri", "bank mandiri", "bri", "bank rakyat indonesia", "bni", "bank negara indonesia",
        "btn", "bank tabungan negara", "bsi", "bank syariah indonesia", "pegadaian",
        "permodalan nasional madani", "pnm", "danareksa", "jasa raharja", "jasindo",
        "asuransi asei", "asei indonesia", "taspen", "asabri", "jamkrindo", "askrindo",
        "ifg", "bahana"
    ],
    "Energi, Minyak & Tambang": [
        "pertamina", "pln", "perusahaan listrik negara", "indonesia power", "nusantara power",
        "mind id", "bukit asam", "aneka tambang", "antam", "timah", "inalum", "pgn",
        "perusahaan gas negara", "elnusa", "pertamina hulu", "pertamina patra niaga"
    ],
    "Infrastruktur, Karya & Semen": [
        "wijaya karya", "wika", "waskita", "adhi karya", "hutama karya", "pt pp", "pembangunan perumahan",
        "brantas abipraya", "nindya karya", "jasa marga", "semen indonesia", "semen padang", "semen gresik",
        "semen tonasa", "perumnas", "krakatau steel", "krakatau medika", "amarta karya"
    ],
    "Transportasi, Logistik & Aviasi": [
        "kereta api indonesia", "kai", "pelindo", "pelabuhan indonesia", "asdp", "pelni",
        "garuda indonesia", "citilink", "gmf aeroasia", "angkasa pura", "damri", "pos indonesia",
        "poslog", "pos logistik", "injourney", "mrt jakarta"
    ],
    "Telekomunikasi & Digital": [
        "telkom", "telkomsel", "metranet", "infomedia", "mitratel", "telkomsat", "telkom akses"
    ],
    "Kesehatan & Farmasi": [
        "bio farma", "kimia farma", "indofarma", "pertamedika", "ihc", "pelindo husada citra"
    ],
    "Pangan, Pertanian & Kehutanan": [
        "bulog", "pupuk indonesia", "petrokimia gresik", "pupuk kujang", "pupuk kaltim", "pusri",
        "pupuk sriwidjaja", "pupuk iskandar muda", "perkebunan nusantara", "ptpn", "rajawali nusantara",
        "id food", "perhutani", "jasa tirta", "berdikari", "sang hyang seri"
    ],
    "Manufaktur, Pertahanan & Jasa Lainnya": [
        "pindad", "dirgantara indonesia", "ptdi", "pal indonesia", "len industri", "dahana",
        "peruri", "sucofindo", "surveyor indonesia", "sarinah"
    ]
}

PARENT_BUMN_KEYWORDS = [
    "persero", "perum", "pt pln", "pt pertamina", "pt telkom", "pal indonesia",
    "dirgantara indonesia", "ptdi", "pindad", "kereta api indonesia", "pos indonesia",
    "garuda indonesia", "pelindo", "pelni", "asdp", "bio farma", "kimia farma", "indofarma",
    "pupuk indonesia", "semen indonesia", "krakatau steel", "wijaya karya", "waskita karya",
    "adhi karya", "hutama karya", "pt pp", "jasa marga", "jasa raharja", "taspen", "asabri",
    "pegadaian", "pnm", "bulog", "perhutani", "jasa tirta", "peruri", "sucofindo",
    "surveyor indonesia", "sarinah", "bank mandiri", "bank rakyat indonesia",
    "bank negara indonesia", "bank tabungan negara", "bank syariah indonesia", "mind id", "antam", "bukit asam", "timah"
]

FALSE_POSITIVE_NAMES = [
    "afwan jaya mandiri", "alisa mandiri", "altima mandiri", "amanullah modis",
    "amilis propertindo", "mukjizat jaya mandiri", "paramita kreasi abadi",
    "advanced specialty chemicals", "agaf global", "agraris muda", "aino indonesia",
    "air surya", "anugerah sawit", "pt digital aplikasi", "pt makassar megaputra",
    "china state construction", "gelora tumbuh hebat", "inkaba", "ardana perkasa",
    "sejahtera kelola", "prima layanan niaga suku cadang", "abuba", "aarya kinari",
    "abadinugraha", "abata indonesia", "abdhi famili", "abhimata persada", "abimanyu",
    "abipraya teknik sentosa", "abisakti surya", "artindo nusa"
]

def classify_company(comp):
    name = (comp.get("name") or "").strip()
    name_lower = name.lower()
    desc = (comp.get("description") or "").lower()
    
    # Check false positives first
    for fp in FALSE_POSITIVE_NAMES:
        if fp in name_lower:
            return None
            
    is_persero = "(persero)" in name_lower or "(persero)" in desc or " persero" in name_lower
    is_perum = "perum " in name_lower or name_lower.startswith("perum ") or "perumahan umum" in desc
    
    detected_cluster = None
    matched_keyword = None
    
    for cluster, kws in BUMN_HOLDINGS.items():
        for kw in kws:
            pattern = r'(?:\b|_)' + re.escape(kw) + r'(?:\b|_)'
            if re.search(pattern, name_lower):
                detected_cluster = cluster
                matched_keyword = kw
                break
        if detected_cluster:
            break
            
    if not detected_cluster:
        if is_persero or is_perum or "bumn" in name_lower or "perseroda" in name_lower:
            for cluster, kws in BUMN_HOLDINGS.items():
                for kw in kws:
                    pattern = r'(?:\b|_)' + re.escape(kw) + r'(?:\b|_)'
                    if re.search(pattern, desc):
                        detected_cluster = cluster
                        matched_keyword = kw
                        break
                if detected_cluster:
                    break
            if not detected_cluster:
                detected_cluster = "BUMN / BUMD Lainnya"

    if not detected_cluster:
        return None
        
    is_parent = False
    if is_persero or is_perum:
        is_parent = True
    elif any(p_kw in name_lower for p_kw in PARENT_BUMN_KEYWORDS):
        is_parent = True

    level = "BUMN Induk (Persero / Perum)" if is_parent else "Anak Perusahaan / Afiliasi BUMN"
    
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', name_lower).strip('-')
    cid = comp.get("id")
    detail_url = f"https://maganghub.kemnaker.go.id/magang-nasional/penyelenggara/{slug}-{cid}"
    
    return {
        "id": cid,
        "name": name,
        "type": level,
        "cluster": detected_cluster,
        "matched_keyword": matched_keyword,
        "vacancies": comp.get("totalActiveVacancies", 0),
        "city": comp.get("city", {}).get("name", "N/A") if comp.get("city") else "N/A",
        "address": comp.get("address") or "",
        "description": comp.get("description") or "",
        "logoUrl": comp.get("logoUrl") or "",
        "url": detail_url
    }
