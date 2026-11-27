# agents.md: istruzioni per gli agenti

## Cos'è questo progetto
PAYSLIP//CORE: dashboard locale in Python + HTML/JS per analizzare le buste paga in PDF (formato "Prospetto Paga" Terna).
- parser.py: estrae dati e voci dai PDF con pdfplumber (usa le coordinate delle parole).
- server.py: server HTTP locale (solo 127.0.0.1). Scansiona la cartella dei PDF, tiene una cache su disco (cache.json) e serve la dashboard.
- static/index.html: interfaccia (Chart.js in static/vendor/, nessuna CDN esterna).

## Regole assolute (repo pubblica)
1. Non committare mai dati personali reali: niente PDF, cache, config locali, nomi, codici fiscali, matricole, IBAN, indirizzi, importi reali.
2. Per i test usa solo PDF sintetici o anonimizzati. Non inserire valori reali in esempi, commenti o test.
3. Non disattivare .gitignore per i file dati. Prima di ogni commit controlla git status e git diff --cached.
4. La cartella di default è configurabile tramite `BUSTE_DIR`: non aggiungere informazioni personali nel codice.

## Come lavorare
- Dipendenze: pip install -r requirements.txt (Python 3.10+).
- Avvio: BUSTE_DIR=/percorso/cartella python3 server.py poi http://127.0.0.1:8765
- Quando cambia il formato dei cedolini o la logica di categorizzazione, incrementa PARSER_VERSION in parser.py: la cache viene ricostruita.
- Voci non riconosciute finiscono in categoria "altro": aggiungi la regola in categoria(), non in modo specifico per una singola busta.
- Il controllo dei totali (competenze, trattenute, netto) deve restare verde su tutte le buste di test.

## Stile del codice
- Modifiche piccole e mirate; nessuna nuova dipendenza senza motivo.
- Il frontend resta un singolo file HTML senza build step.
- Interfaccia e testi per l'utente in italiano.

## Home banking
- `bank.py` legge file `.xls`/`.xlsx` solo quando `bank_enabled` è attivo. Descrizioni e dettagli dei movimenti restano esclusivamente in memoria durante la sessione e non vanno scritti in cache, log o repository.
- Non salvare né mostrare numeri carta o IBAN. Non committare estratti conto, cache bancaria, configurazioni locali o nomi personali.
- Prove esclusivamente con fixture sintetiche; controllare `git status` prima di consegnare.

## Altri redditi
- `static/extra.js` + API `/api/extra`: compensi fuori busta paga salvati in `extra.json` (mai in repo). Formule fiscali in testa a `extra.js`: aggiornale ogni anno.
- Il server accetta solo richieste con Host/Origin locali (`allowed()`): non rimuovere il controllo.
- Due temi scelti dall'utente (`data-theme` su `<html>`, selettore in header): «sobrio» (predefinito, chiaro/scuro automatico) e «futuristico». Il sobrio usa variabili CSS e palette desaturata; i colori neon del futuristico sono la mappa `NEON` in `index.html`. Nuovi colori: aggiungili alla palette sobria e alla mappa `NEON`.
