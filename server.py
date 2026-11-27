#!/usr/bin/env python3
"""Server locale: scansiona la cartella dei PDF, parsa solo i nuovi/modificati (cache su disco) e serve la dashboard."""
import json, os, sys, threading, time, tempfile, hashlib
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, unquote
from parser import parse_pdf, PARSER_VERSION
import bank

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(BASE, "config.json"); CACHE = os.path.join(BASE, "cache.json"); BCACHE = os.path.join(BASE, "cache_bank.json"); EXTRA = os.path.join(BASE, "extra.json")
DEFAULT_DIR = os.environ.get("BUSTE_DIR", os.path.dirname(BASE))
LOCK = threading.Lock()
CONFIG_LOCK = threading.Lock()

def load(path, default):
    try:
        with open(path, encoding="utf-8") as f: return json.load(f)
    except Exception: return default

def save(path, data):
    fd, tmp = tempfile.mkstemp(prefix="." + os.path.basename(path) + ".", suffix=".tmp", dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False)
        os.replace(tmp, path)
    finally:
        try: os.unlink(tmp)
        except FileNotFoundError: pass

def get_dir(): return os.path.expanduser(load(CONFIG, {}).get("directory", DEFAULT_DIR))

def scan(force=False):
    """Aggiorna la cache: parsa solo i file nuovi o cambiati (size+mtime), rimuove quelli spariti."""
    with LOCK:
        d = get_dir(); cache = load(CACHE, {})
        if cache.get("version") != PARSER_VERSION or cache.get("dir") != d or force: cache = {"version": PARSER_VERSION, "dir": d, "files": {}}
        files, errors, changed = cache["files"], [], False
        if not os.path.isdir(d): return {"directory": d, "exists": False, "payslips": [], "annual_totals": {}, "errors": [], "updated": time.time()}
        presenti = set()
        for root, _, names in os.walk(d):
            for n in names:
                if not n.lower().endswith(".pdf"): continue
                p = os.path.join(root, n); st = os.stat(p); sig = [st.st_size, st.st_mtime_ns]; presenti.add(p)
                if p in files and files[p].get("sig") == sig:
                    if not files[p].get("sha256"):
                        try:
                            with open(p, "rb") as pdf: files[p]["sha256"] = hashlib.sha256(pdf.read()).hexdigest()
                            changed = True
                        except OSError: pass
                    continue
                try: files[p] = {"sig": sig, "data": parse_pdf(p)}; files[p]["data"]["file"] = n
                except Exception as e: files[p] = {"sig": sig, "error": str(e)}
                try:
                    with open(p, "rb") as pdf: files[p]["sha256"] = hashlib.sha256(pdf.read()).hexdigest()
                except OSError: pass
                changed = True
        for p in list(files):
            if p not in presenti: del files[p]; changed = True
        if changed or not os.path.exists(CACHE): save(CACHE, cache)
        per = {}  # una sola busta per periodo: vince il file modificato per ultimo
        for f in sorted((f for f in files.values() if "data" in f), key=lambda f: f["sig"][1]): per[f["data"]["periodo"]] = f["data"]
        pay = [per[k] for k in sorted(per)]
        # Annual totals include every distinct parsed PDF, including multiple payslips
        # in the same month. Exact copies are deduplicated by file content.
        annual, seen = {}, set()
        for f in files.values():
            if "data" not in f: continue
            digest = f.get("sha256")
            if digest and digest in seen: continue
            if digest: seen.add(digest)
            data = f["data"]
            net = data.get("campi", {}).get("netto")
            if not isinstance(net, (int, float)): continue
            year = str(data["anno"]); month = int(data["mese"])
            row = annual.setdefault(year, {"netto": 0, "buste": 0, "mesi": []})
            row["netto"] += net
            row["buste"] += 1
            if month not in row["mesi"]: row["mesi"].append(month)
        for row in annual.values(): row["mesi"].sort()
        errors = [{"file": os.path.basename(p), "errore": f["error"]} for p, f in files.items() if "error" in f]
        return {"directory": d, "exists": True, "payslips": pay, "annual_totals": annual, "errors": errors, "updated": time.time()}

def cfg(): return load(CONFIG, {})
def bank_dir(): return os.path.expanduser(cfg().get("bank_dir") or os.path.join(get_dir(), "home_banking"))
def settings():
    c = cfg()
    return {"directory": get_dir(), "default": DEFAULT_DIR, "bank_enabled": bool(c.get("bank_enabled")), "bank_dir": bank_dir(),
            "budget": c.get("budget", {}), "bank_map": c.get("bank_map", {}), "extra_cfg": c.get("extra_cfg", {}), "defaults": bank.defaults()}
def clean_extra(items):
    """Valida e normalizza gli altri redditi (restano solo in locale, extra.json)."""
    out = []
    for i in items[:2000] if isinstance(items, list) else []:
        if not isinstance(i, dict): continue
        try: imp = round(float(i.get("importo", 0)), 2)
        except (TypeError, ValueError): continue
        d = str(i.get("data", ""))[:10]
        if not (len(d) == 10 and d[4] == "-" and d[7] == "-" and imp >= 0): continue
        out.append({"id": str(i.get("id", ""))[:32] or str(len(out)), "data": d, "descrizione": str(i.get("descrizione", ""))[:80],
                    "importo": imp, "incassato": bool(i.get("incassato")), "ritenuta": bool(i.get("ritenuta"))})
    return out
def extra_data(): return {"items": clean_extra(load(EXTRA, {}).get("items", []))}
def bank_data(force=False):
    if not cfg().get("bank_enabled"): return {"enabled": False}
    with LOCK: return bank.scan_bank(bank_dir(), BCACHE, force)

class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=os.path.join(BASE, "static"), **k)
    def log_message(self, *a): pass
    def send_json(self, obj, code=200):
        b = json.dumps(obj, ensure_ascii=False).encode(); self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def allowed(self):
        """Difesa da richieste di altri siti (CSRF / DNS rebinding): Host e Origin devono essere locali."""
        port = self.server.server_address[1]; ok = {f"127.0.0.1:{port}", f"localhost:{port}"}
        if self.headers.get("Host", "") not in ok: return False
        o = self.headers.get("Origin")
        return o is None or o in {f"http://{h}" for h in ok}
    def do_GET(self):
        if not self.allowed(): return self.send_json({"error": "origine non consentita"}, 403)
        path = urlparse(self.path).path
        if path == "/api/data": return self.send_json(scan())
        if path == "/api/config": return self.send_json({"directory": get_dir(), "default": DEFAULT_DIR})
        if path == "/api/settings": return self.send_json(settings())
        if path == "/api/bank": return self.send_json(bank_data())
        if path == "/api/extra": return self.send_json(extra_data())
        return super().do_GET()
    def do_POST(self):
        if not self.allowed(): return self.send_json({"error": "origine non consentita"}, 403)
        path = urlparse(self.path).path
        if path == "/api/bank/upload":   # carica un estratto conto nella cartella home banking
            if not cfg().get("bank_enabled"): return self.send_json({"error": "home banking disattivato"}, 403)
            try: size = int(self.headers.get("Content-Length", "0"))
            except ValueError: return self.send_json({"error": "dimensione non valida"}, 400)
            if size <= 0: return self.send_json({"error": "file vuoto"}, 400)
            if size > 25_000_000: return self.send_json({"error": "file troppo grande (max 25 MB)"}, 413)
            raw = self.rfile.read(size)
            if len(raw) != size: return self.send_json({"error": "upload incompleto"}, 400)
            name = os.path.basename(unquote(self.headers.get("X-Filename", "estratto.xlsx"))) or "estratto.xlsx"
            if not name.lower().endswith((".xls", ".xlsx")): return self.send_json({"error": "formato non supportato"}, 400)
            d = bank_dir(); os.makedirs(d, exist_ok=True)
            today = time.strftime("%Y-%m-%d")
            stem, ext = os.path.splitext(name)
            ext = ext.lower()
            dest = os.path.join(d, f"{today}_{stem}{ext}")
            # O_EXCL impedisce collisioni anche fra richieste simultanee.
            index = 1
            while True:
                try:
                    with open(dest, "xb") as f: f.write(raw)
                    break
                except FileExistsError:
                    dest = os.path.join(d, f"{today}_{stem}_{index}{ext}"); index += 1
            result = bank_data(force=True)
            uploaded = os.path.basename(dest)
            file_error = next((item for item in result.get("errors", []) if item.get("file") == uploaded), None)
            if file_error:
                return self.send_json({"error": f"{uploaded}: {file_error['errore']}", "saved": uploaded}, 422)
            result["uploaded"] = uploaded
            return self.send_json(result)
        if path not in ("/api/config", "/api/settings", "/api/rescan", "/api/extra"):
            return self.send_json({"error": "not found"}, 404)
        try: size = int(self.headers.get("Content-Length", "0") or 0)
        except ValueError: return self.send_json({"error": "dimensione non valida"}, 400)
        if size > 1_000_000: return self.send_json({"error": "richiesta troppo grande"}, 413)
        raw = self.rfile.read(size)
        try: body = json.loads(raw or b"{}")
        except (json.JSONDecodeError, UnicodeDecodeError): return self.send_json({"error": "JSON non valido"}, 400)
        if not isinstance(body, dict): return self.send_json({"error": "JSON non valido"}, 400)
        if path == "/api/extra":
            with CONFIG_LOCK: save(EXTRA, {"items": clean_extra(body.get("items"))})
            return self.send_json(extra_data())
        if path == "/api/config":
            with CONFIG_LOCK:
                c = cfg(); c["directory"] = os.path.expanduser((body.get("directory") or "").strip() or DEFAULT_DIR); save(CONFIG, c)
            return self.send_json(scan())
        if path == "/api/settings":
            with CONFIG_LOCK:
                c = cfg()
                if "bank_enabled" in body: c["bank_enabled"] = bool(body["bank_enabled"])
                if "bank_dir" in body: c["bank_dir"] = str(body["bank_dir"]).strip()
                if isinstance(body.get("budget"), dict): c["budget"] = body["budget"]
                if isinstance(body.get("extra_cfg"), dict):
                    x = body["extra_cfg"]; c["extra_cfg"] = {"metodo": "lordo" if x.get("metodo") == "lordo" else "netto",
                        "addizionali_pct": min(max(float(x.get("addizionali_pct") or 0), 0), 5), "base_override": max(float(x.get("base_override") or 0), 0)}
                if isinstance(body.get("bank_map"), dict): c["bank_map"] = {str(k): str(v) for k, v in body["bank_map"].items()}
                save(CONFIG, c)
            return self.send_json(settings())
        if path == "/api/rescan": bank_data(True); return self.send_json(scan(force=True))
        self.send_json({"error": "not found"}, 404)

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    print(f"Cartella buste paga: {get_dir()}\nDashboard: http://127.0.0.1:{port}")
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
