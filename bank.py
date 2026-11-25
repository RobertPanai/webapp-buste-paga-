"""Lettore estratti conto home banking (xls/xlsx): movimenti, dedup tra file, cache su disco."""
import io, os, re, warnings
from datetime import datetime

BANK_VERSION = 1
# Movimenti e descrizioni restano solo in memoria e vengono ricreati dopo il riavvio.
_MEMORY = {}
SECTORS = [  # id, etichetta, tipo, colore
 ("casa", "Casa & utenze", "spesa", "#7aa8ff"), ("cibo", "Alimentari", "spesa", "#a3ff12"), ("ristoranti", "Ristoranti e bar", "spesa", "#ffb020"),
 ("trasporti", "Auto & trasporti", "spesa", "#22e4ff"), ("salute", "Salute & persona", "spesa", "#34d399"), ("svago", "Svago, sport & viaggi", "spesa", "#ff2bd6"),
 ("contanti", "Prelievi e bonifici", "spesa", "#94a3b8"), ("altro", "Altro", "spesa", "#64748b"),
 ("risparmio", "Salvadanaio / investimenti", "risparmio", "#8b5cf6"), ("disinv", "Prelievi dal salvadanaio", "disinv", "#c084fc"),
 ("stipendio", "Stipendio", "entrata", "#2dd4bf"), ("entrate", "Altre entrate", "entrata", "#60a5fa")]
MAP = {"Pagamento affitti": "casa", "Casa varie": "casa", "Rate Mutuo e Finanziamento": "casa", "TV, Internet, telefono": "casa", "Cellulare": "casa",
 "Generi alimentari e supermercato": "cibo", "Ristoranti e bar": "ristoranti", "Carburanti": "trasporti", "Manutenzione veicoli": "trasporti",
 "Trasporti, noleggi, taxi e parcheggi": "trasporti", "Treno, aereo, nave": "trasporti", "Spese mediche": "salute", "Cura della persona": "salute",
 "Corsi e sport": "svago", "Tempo libero varie": "svago", "Viaggi e vacanze": "svago", "Hi-tech e informatica": "svago", "Prelievi": "contanti",
 "Bonifici in uscita": "contanti", "Altre uscite": "altro", "Addebiti vari": "altro", "Investimenti, BDR e Salvadanaio": "risparmio",
 "Disinvestimenti, BDR e Salvadanaio": "disinv", "Stipendi e pensioni": "stipendio", "Bonifici ricevuti": "entrate",
 "Rimborsi spese mediche": "entrate", "Rimborsi spese e storni": "entrate"}

def defaults(): return {"sectors": [{"id": a, "label": b, "kind": c, "color": d} for a, b, c, d in SECTORS], "map": MAP}

def _rows(path):
    data = open(path, "rb").read()
    if data[:2] == b"PK":
        import openpyxl
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True, read_only=True)
            return [list(r) for r in wb.worksheets[0].iter_rows(values_only=True)]
    import xlrd  # vero .xls (BIFF)
    sh = xlrd.open_workbook(file_contents=data).sheet_by_index(0)
    return [[sh.cell_value(r, c) for c in range(sh.ncols)] for r in range(sh.nrows)]

def _date(v):
    if isinstance(v, datetime): return v.strftime("%Y-%m-%d")
    m = re.match(r"(\d{2})/(\d{2})/(\d{4})", str(v or ""))
    if m: return f"{m[3]}-{m[2]}-{m[1]}"
    m = re.match(r"(\d{4}-\d{2}-\d{2})", str(v or ""))
    return m[1] if m else None

def _num(v):
    if isinstance(v, (int, float)): return float(v)
    try: return float(str(v).replace(".", "").replace(",", ".")) if "," in str(v) else float(v)
    except Exception: return None

def parse_bank(path):
    rows = _rows(path); h = None
    for i, r in enumerate(rows):
        low = [str(c or "").strip().lower() for c in r]
        if "data" in low and "importo" in low: h = (i, {n: low.index(n) for n in ("data", "operazione", "categoria", "importo") if n in low}); break
    if not h: raise ValueError("intestazione (Data/Importo) non trovata")
    ix, mov = h[1], []
    for r in rows[h[0] + 1:]:
        d = _date(r[ix["data"]]) if len(r) > ix["data"] else None; i = _num(r[ix["importo"]]) if len(r) > ix["importo"] else None
        if not d or i is None: continue
        g = lambda k: str(r[ix[k]] or "").strip() if k in ix and len(r) > ix[k] else ""
        mov.append({"d": d, "o": g("operazione")[:60], "c": g("categoria"), "i": round(i, 2)})
    return mov

def scan_bank(folder, cache_path, force=False):
    files = _MEMORY.setdefault(folder, {})
    if force: files.clear()
    errors = []
    seen = set()
    if os.path.isdir(folder):
        for root, _, names in os.walk(folder):
            for n in names:
                if n.startswith((".", "~")) or not n.lower().endswith((".xls", ".xlsx")): continue
                p = os.path.join(root, n); st = os.stat(p); sig = [st.st_size, st.st_mtime_ns]; seen.add(p)
                if p in files and files[p]["sig"] == sig: continue
                try: files[p] = {"sig": sig, "mov": parse_bank(p)}
                except Exception: files[p] = {"sig": sig, "error": "file non leggibile o formato non riconosciuto"}
                changed = True
    for p in list(files):
        if p not in seen: del files[p]
    best, info = {}, []   # stesso movimento in più file (periodi sovrapposti): si tiene il massimo numero di occorrenze
    for p, f in sorted(files.items()):
        if "error" in f: errors.append({"file": os.path.basename(p), "errore": f["error"]}); continue
        cnt = {}
        for t in f["mov"]: k = (t["d"], t["o"], t["c"], t["i"]); cnt[k] = cnt.get(k, 0) + 1
        for k, c in cnt.items(): best[k] = max(best.get(k, 0), c)
        ds = [t["d"] for t in f["mov"]]
        info.append({"name": os.path.basename(p), "n": len(ds), "from": min(ds) if ds else None, "to": max(ds) if ds else None})
    mov = [{"d": k[0], "o": k[1], "c": k[2], "i": k[3]} for k, c in best.items() for _ in range(c)]
    mov.sort(key=lambda t: t["d"], reverse=True)
    return {"enabled": True, "dir": folder, "exists": os.path.isdir(folder), "movimenti": mov, "files": info, "errors": errors,
            "sig": "|".join(f"{x['name']}:{x['n']}" for x in info) + f"|{len(mov)}"}
