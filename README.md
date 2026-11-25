# PAYSLIP//CORE
Dashboard locale per le buste paga Terna (PDF).

## Avvio rapido

Dalla cartella `buste-dashboard`, esegui `./buste_paga`. Per poterla richiamare
con il solo comando `buste_paga`, imposta l'alias esistente affinché punti al
percorso completo di questo script, ad esempio:

    alias buste_paga='/percorso/del/progetto/buste-dashboard/buste_paga'

Lo script avvia questa dashboard e usa la cartella principale del progetto come
cartella dei PDF; `BUSTE_DIR` può sovrascrivere il percorso. Il server resta
accessibile solo all'indirizzo locale configurato dall'applicazione.

    pip3 install -r requirements.txt
    python3 server.py            # poi apri http://127.0.0.1:8765

- Cartella di default: la cartella che contiene il progetto (cambiabile dal pulsante ⚙ Cartella, salvata in `config.json`).
- Cache in `cache.json`: vengono letti solo i PDF nuovi o modificati; la pagina si aggiorna da sola ogni 10 s. «Rileggi tutto» svuota la cache.
- Ogni busta è validata: somma voci = totale competenze/trattenute e netto (badge verde/rosso in «Dettaglio»).
- Nuove voci non riconosciute finiscono in «Altro»: aggiungi la regola in `categoria()` di `parser.py` e incrementa `PARSER_VERSION`.

## Home banking (opzionale)
Attivalo da ⚙ Cartella → «Analizza anche l'home banking». Senza attivarlo l'app mostra solo le buste paga.
- Estratti conto `.xls`/`.xlsx` (elenco operazioni della banca) nella cartella `home_banking` dentro la cartella buste paga, oppure con «Carica file» nella scheda Banca. I movimenti già presenti non si duplicano.
- Schede: **Banca** (entrate/spese, settori, ricorrenti, collegamento col netto in busta), **Budget** (limite per settore in % del reddito o in €, quota da risparmiare, mappa categorie banca → settore), **Movimenti**.
- I file Excel e `cache_bank.json` sono nel `.gitignore`: non vanno mai in repo.
