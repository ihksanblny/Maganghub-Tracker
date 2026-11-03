# Maganghub BUMN Finder & Scraper (Kemnaker RI)

Aplikasi web interaktif dan scraper cerdas untuk mencari dan memfilter seluruh perusahaan **BUMN (Badan Usaha Milik Negara)** beserta **Anak Perusahaan / Afiliasi** yang terdaftar pada portal resmi [Program Pemagangan Kemnaker RI (Maganghub)](https://maganghub.kemnaker.go.id/magang-nasional/penyelenggara).

---

## 🌟 Fitur Utama

1. **Scraper Cepat & Multithreaded (`scraper.py`)**:
   - Mengambil data perusahaan langsung dari API SSR Maganghub Kemnaker dengan 6 pekerja paralel (selesai dalam ~25 detik).
   - Menghasilkan dataset lengkap dengan **445 entitas BUMN** dan **6.350+ lowongan aktif**.
   - Otomatis mengekspor ke format **JSON** (`data/bumn_maganghub.json`) dan **CSV (Excel-Ready UTF-8 BOM)** (`data/bumn_maganghub.csv`).

2. **Klasifikasi Cerdas BUMN (`bumn_classifier.py`)**:
   - Membedakan **BUMN Induk (Persero / Perum)** vs **Anak Perusahaan / Cucu / Afiliasi BUMN**.
   - Mengelompokkan berdasarkan klaster sektor industri:
     - Perbankan & Jasa Keuangan (Mandiri, BRI, BNI, BTN, BSI, Pegadaian, PNM, dll.)
     - Energi, Minyak & Tambang (Pertamina, PLN, MIND ID, Antam, Timah, dll.)
     - Infrastruktur & Konstruksi (WIKA, Waskita, Adhi Karya, Hutama Karya, PTPP, Semen Indonesia, dll.)
     - Transportasi & Logistik (KAI, Pelindo, ASDP, Garuda Indonesia, Angkasa Pura, DAMRI, dll.)
     - Telekomunikasi & Teknologi (Telkom, Telkomsel, Metranet, dll.)
     - Kesehatan & Farmasi (Bio Farma, Kimia Farma, Pertamedika IHC, dll.)
     - Pangan & Pertanian (Bulog, Pupuk Indonesia, PTPN, Perhutani, Jasa Tirta, dll.)
     - Manufaktur & Pertahanan (Pindad, PTDI, PAL Indonesia, LEN, Peruri, dll.)
   - Memfilter false-positives (perusahaan swasta dengan nama kebetulan mengandung kata kunci).

3. **Dashboard Web Interaktif (`app.py` & `web/index.html`)**:
   - **Zero External Dependencies**: Berjalan menggunakan standard library Python (`http.server`), tidak memerlukan `pip install` tambahan.
   - Pencarian instan (real-time filtering nama perusahaan, deskripsi, posisi, kota).
   - Filter berdasarkan Sektor / Klaster dan Lokasi Kota / Wilayah.
   - Filter Tipe: Semua, BUMN Induk (Persero/Perum), atau Anak Perusahaan.
   - Toggle "Hanya yang memiliki lowongan aktif (> 0)".
   - Tombol langsung untuk **Buka di Maganghub** (ke halaman registrasi resmi Kemnaker).
   - Tombol **Unduh CSV** dan tombol **Sinkron Data** (rescrape langsung dari web).

---

## 🚀 Cara Menjalankan

### 1. Menjalankan Website (Web Dashboard)

Cukup jalankan perintah berikut di terminal:

```bash
python app.py
```

Buka browser Anda di alamat:
👉 **[http://localhost:8000](http://localhost:8000)** (atau port yang ditampilkan di terminal).

### 2. Menjalankan Scraper Secara Manual (CLI)

Untuk memperbarui data kapan saja dari portal Maganghub Kemnaker:

```bash
python scraper.py
```

Hasil scraping akan otomatis diperbarui di:
- `data/bumn_maganghub.json`
- `data/bumn_maganghub.csv`

---

## 📂 Struktur File

```
maganghub/
├── app.py                   # Server web & REST API lokal (Zero dependencies)
├── scraper.py               # Multithreaded scraper untuk Maganghub Kemnaker
├── bumn_classifier.py       # Engine pengklasifikasi entitas & sektor BUMN
├── web/
│   └── index.html           # UI Dashboard interaktif (Tailwind CSS + Lucide)
├── data/
│   ├── bumn_maganghub.json  # Data terstruktur BUMN (JSON)
│   └── bumn_maganghub.csv   # Data terstruktur BUMN (CSV siap buka di Excel)
└── README.md                # Dokumentasi proyek
```

---

## 🔗 Endpoint REST API Lokal

Saat `app.py` berjalan, Anda juga dapat mengakses endpoint API berikut:

| Method | Endpoint | Deskripsi |
|---|---|---|
| `GET` | `/api/bumn` | Mengambil daftar BUMN (Mendukung parameter `?q=`, `?cluster=`, `?type=`, `?city=`, `?vacancies_only=1`, `?sort=`) |
| `GET` | `/api/stats` | Statistik ringkasan (total entitas, lowongan, distribusi sektor & kota) |
| `GET` | `/api/download/csv` | Mengunduh file CSV langsung |
| `POST` | `/api/rescrape` | Memicu sinkronisasi data ulang di latar belakang |

