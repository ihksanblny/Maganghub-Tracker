import os
import sys
import json
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socket

# Ensure proper encoding
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
JSON_PATH = os.path.join(DATA_DIR, "bumn_maganghub.json")
CSV_PATH = os.path.join(DATA_DIR, "bumn_maganghub.csv")
WEB_DIR = os.path.join(BASE_DIR, "web")

def load_data():
    if not os.path.exists(JSON_PATH):
        # Auto scrape if not exists
        print("Data belum tersedia. Menjalankan scraper awal...")
        import scraper
        scraper.run_scraper()
    
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

class MaganghubServerHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # Clean logging
        sys.stderr.write(f"[{self.log_date_time_string()}] {args[0]} - {args[1]}\n")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if path == "/" or path == "/index.html":
            html_file = os.path.join(WEB_DIR, "index.html")
            if os.path.exists(html_file):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                with open(html_file, "rb") as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_error(404, "Index HTML not found")
                return

        elif path == "/api/bumn":
            data = load_data()
            query = params.get("q", [""])[0].lower().strip()
            cluster = params.get("cluster", [""])[0].strip()
            bumn_type = params.get("type", [""])[0].strip()
            city = params.get("city", [""])[0].strip()
            vacancies_only = params.get("vacancies_only", ["0"])[0] in ["1", "true"]
            sort_by = params.get("sort", ["vacancies_desc"])[0]

            filtered = []
            for item in data:
                if query:
                    name_match = query in item.get("name", "").lower()
                    desc_match = query in item.get("description", "").lower()
                    city_match = query in item.get("city", "").lower()
                    cluster_match = query in item.get("cluster", "").lower()
                    if not (name_match or desc_match or city_match or cluster_match):
                        continue

                if cluster and item.get("cluster") != cluster:
                    continue

                if city and item.get("city") != city:
                    continue

                if bumn_type == "induk" and "Induk" not in item.get("type", ""):
                    continue
                elif bumn_type == "anak" and "Anak" not in item.get("type", ""):
                    continue

                if vacancies_only and item.get("vacancies", 0) <= 0:
                    continue

                filtered.append(item)

            if sort_by == "vacancies_desc":
                filtered.sort(key=lambda x: (-x.get("vacancies", 0), x.get("name", "")))
            elif sort_by == "name_asc":
                filtered.sort(key=lambda x: x.get("name", ""))
            elif sort_by == "city_asc":
                filtered.sort(key=lambda x: x.get("city", ""))

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(filtered, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/api/stats":
            data = load_data()
            total_vacancies = sum(c.get("vacancies", 0) for c in data)
            induk_count = sum(1 for c in data if "Induk" in c.get("type", ""))
            anak_count = sum(1 for c in data if "Anak" in c.get("type", ""))

            clusters = {}
            cities = {}
            for c in data:
                cl = c.get("cluster", "Lainnya")
                clusters[cl] = clusters.get(cl, 0) + 1
                ct = c.get("city", "N/A")
                if ct != "N/A":
                    cities[ct] = cities.get(ct, 0) + 1

            stats = {
                "total_companies": len(data),
                "total_vacancies": total_vacancies,
                "induk_count": induk_count,
                "anak_count": anak_count,
                "clusters": clusters,
                "top_cities": dict(sorted(cities.items(), key=lambda x: -x[1])[:10])
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(stats, ensure_ascii=False).encode("utf-8"))
            return

        elif path == "/api/download/csv":
            if os.path.exists(CSV_PATH):
                self.send_response(200)
                self.send_header("Content-Type", "text/csv; charset=utf-8")
                self.send_header("Content-Disposition", 'attachment; filename="bumn_maganghub_kemnaker.csv"')
                self.end_headers()
                with open(CSV_PATH, "rb") as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_error(404, "CSV file not found")
                return

        # Fallback to standard handler for any other static files
        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/rescrape":
            try:
                import scraper
                print("Memicu pembaruan data scraper...")
                updated_data = scraper.run_scraper()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "total_companies": len(updated_data),
                    "message": "Data berhasil diperbarui dari Maganghub Kemnaker"
                }).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        self.send_error(404, "Endpoint not found")

def find_available_port(start_port=8000, max_tries=10):
    for port in range(start_port, start_port + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return start_port

def start_server(port=None):
    if port is None:
        port = find_available_port(8000)

    server = HTTPServer(("0.0.0.0", port), MaganghubServerHandler)
    print("=" * 65)
    print("🚀 MAGANGHUB BUMN FINDER - WEB APPLICATION")
    print("=" * 65)
    print(f"Server aktif dan dapat diakses di:")
    print(f"  👉 Lokal   : http://localhost:{port}")
    print(f"  👉 Jaringan: http://127.0.0.1:{port}")
    print("=" * 65)
    print("Tekan Ctrl+C untuk menghentikan server.")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer dihentikan.")
        server.server_close()

if __name__ == "__main__":
    port_arg = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else None
    start_server(port_arg)

