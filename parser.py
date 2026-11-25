"""Parser dei cedolini Terna (Prospetto Paga) -> dict. Usa le coordinate delle parole nel PDF."""
import re, pdfplumber

PARSER_VERSION = 1
MESI = ["gennaio","febbraio","marzo","aprile","maggio","giugno","luglio","agosto","settembre","ottobre","novembre","dicembre"]
NUM = re.compile(r"^-?\d{1,3}(\.\d{3})*,\d+$|^-?\d+,\d+$")
AREE = {"N_IT", "G_TER", "E_FISC"}

def num(s): return float(s.replace(".", "").replace(",", "."))

# (nome campo, regex etichetta, pagina "any")
CAMPI = {
 "netto": r"Netto a pagare", "tot_competenze": r"Totale Competenze", "tot_trattenute": r"Totale Trattenute",
 "imponibile_fiscale": r"Imponibile Fiscale", "imposta_lorda": r"Imposta lorda", "detrazioni": r"Detr\.spett\.lav\.dip/Ul\.Det",
 "imponibile_prev": r"Imp\.previd\.non arrot\.", "retrib_utile_tfr": r"Retrib\. Utile TFR", "quota_tfr": r"Quota matur\.TFR Lordo",
 "ctr_fpc_dip": r"CTR F\.P\.C\. Dip\.te", "ctr_fpc_az": r"CTR F\.P\.C\. azienda", "ctr_fpc_tot": r"Totale CTR F\.P\.C\.",
 "cong_credito": r"Conguaglio a credito", "cong_debito": r"Conguaglio a debito",
 "ferie_residuo": r"FERIE Residuo(?! AP)", "exfest_residuo": r"EX FESTIVITA' Residuo(?! AP)", "rol_residuo": r"ROL Residuo",
 "prog_imponibile_fisc": r"Impon\.Fisc\.Progr\.", "prog_imposta_netta": r"Imposta Netta Prog\.", "prog_ivs": r"Contributo IVS",
 "prog_imponibile_prev": r"Imp\.IVS Arr\./Imp IVS agg\.", "prog_tfr": r"Quota LordaTFR A\.C\.", "prog_cigs": r"Contributi CIGS",
 "prog_detrazioni": r"Tot\.Detr\.Prog\.", "prog_fpc_dip": r"Contributo C/Dip\.", "prog_fpc_az": r"Contributo C/AZ",
}

def categoria(code, desc):
    d = desc.lower()
    if code == "V_01000": return "retribuzione"
    if code == "V_EDR": return "indennita"
    if code in ("Q_ST0021", "Q_ST0023", "Q_ST0022") or "contrib. c/dip" in d and "compl" not in d: return "inps"
    if code == "V_70004" or "prev. complementare" in d: return "prev_compl"
    if code == "Q_ST0003" or d.startswith("irpef"): return "irpef"
    if code.startswith("Q_O0") and "addizional" in d: return "addizionali"
    if code in ("Q_O0167",) or "addizionale" in d: return "addizionali"
    if "welfare" in d or "fringe" in d: return "welfare"
    if "l.199/25" in d or "detass" in d or "tax separata" in d: return "imposte_sost"
    if "str progr" in d or "straord" in d and not d.startswith("contrib"): return "straordinari"
    if "ore viaggio" in d: return "viaggio"
    if any(k in d for k in ("rimb", "spese", "varie di viaggio", "ass.to trasferta", "trasferta", "piccole spese")): return "rimborsi"
    if "welfare" in d or "fringe" in d: return "welfare"
    if any(k in d for k in ("ristorant", "mensa", " tk ", "tk supp")): return "mensa"
    if "premio" in d: return "premi"
    if "ferie" in d or "festivit" in d: return "assenze"
    return "altro"

def _valore(page, words, label_rx):
    best = None
    for m in page.search(label_rx):
        for w in words:
            if not NUM.match(w["text"]): continue
            dy = w["top"] - m["top"]
            if 2 <= dy <= 26 and m["x0"] - 4 <= w["x1"] <= m["x0"] + 115:
                if best is None or (dy, w["x0"]) < best[0]: best = ((dy, w["x0"]), num(w["text"]))
        if best: break  # prima occorrenza (in ordine di pagina) che ha un valore
    return best[1] if best else None

def parse_pdf(path):
    out = {"campi": {}, "voci": []}
    with pdfplumber.open(path) as pdf:
        testo = ""
        for page in pdf.pages:
            words = page.extract_words(keep_blank_chars=False)
            testo += (page.extract_text() or "") + "\n"
            for k, rx in CAMPI.items():
                if k in out["campi"]: continue
                v = _valore(page, words, rx)
                if v is not None: out["campi"][k] = v
            righe = []
            for w in sorted(words, key=lambda w: w["top"]):
                if righe and abs(w["top"] - righe[-1][0]["top"]) < 3: righe[-1].append(w)
                else: righe.append([w])
            for ws in righe:
                ws.sort(key=lambda w: w["x0"])
                if len(ws) < 3 or ws[0]["text"] not in AREE or not re.match(r"^[A-Z]_", ws[1]["text"]): continue
                v = {"area": ws[0]["text"], "codice": ws[1]["text"], "descrizione": [], "competenza": None, "quantita": None, "dato_base": None, "trattenuta": 0.0, "competenza_importo": 0.0}
                for w in ws[2:]:
                    t = w["text"]
                    if re.match(r"^\d\d/\d{4}$", t): v["competenza"] = t
                    elif NUM.match(t):
                        x = w["x1"]; n = num(t)
                        if x < 385: v["quantita"] = n
                        elif x < 435: v["dato_base"] = n
                        elif x < 500: v["trattenuta"] = n
                        else: v["competenza_importo"] = n
                    elif t != "*" and w["x0"] < 335: v["descrizione"].append(t)
                v["descrizione"] = " ".join(v["descrizione"])
                v["categoria"] = categoria(v["codice"], v["descrizione"])
                v["tipo"] = "competenza" if v["competenza_importo"] else "trattenuta" if v["trattenuta"] else "info"
                out["voci"].append(v)
    m = re.search(r"(%s)\s+(20\d\d)" % "|".join(MESI), testo, re.I)
    if not m: raise ValueError("periodo non trovato")
    out["anno"], out["mese"] = int(m.group(2)), MESI.index(m.group(1).lower()) + 1
    out["periodo"] = f"{out['anno']}-{out['mese']:02d}"
    c = out["campi"]
    cong = c.get("cong_credito", 0) - c.get("cong_debito", 0)
    if abs(cong) > 0.005:
        out["voci"].append({"area": "E_FISC", "codice": "CONG", "descrizione": "Conguaglio fiscale " + ("a credito" if cong > 0 else "a debito"),
            "competenza": f"{out['mese']:02d}/{out['anno']}", "quantita": None, "dato_base": None,
            "trattenuta": -cong if cong < 0 else 0.0, "competenza_importo": cong if cong > 0 else 0.0, "categoria": "conguaglio", "tipo": "competenza" if cong > 0 else "trattenuta"})
    sc = round(sum(v["competenza_importo"] for v in out["voci"]), 2); st = round(sum(v["trattenuta"] for v in out["voci"]), 2)
    out["controlli"] = {"competenze_ok": abs(sc - c.get("tot_competenze", -1)) < 0.02, "trattenute_ok": abs(st - c.get("tot_trattenute", -1)) < 0.02,
                        "netto_ok": abs(c.get("tot_competenze", 0) - c.get("tot_trattenute", 0) - c.get("netto", -1)) < 0.02}
    return out
