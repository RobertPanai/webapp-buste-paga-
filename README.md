# PAYSLIP//CORE
Dashboard locale per le buste paga Terna (PDF).

## Avvio rapido

Dalla cartella del progetto, esegui `./buste_paga`. Per poterla richiamare con
il solo comando `buste_paga`, imposta l'alias esistente affinché punti al
percorso completo di questo script nella cartella principale, ad esempio:

    alias buste_paga='/percorso/del/progetto/buste_paga'

Lo script avvia questa dashboard e usa la cartella del progetto come cartella
dei PDF; `BUSTE_DIR` può sovrascrivere il percorso. Il server resta accessibile
solo all'indirizzo locale configurato dall'applicazione.

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

## Altri redditi e stima 730
La scheda **Altri redditi** registra i compensi fuori busta paga (es. prestazioni occasionali): importo netto, se è già incassato o da incassare, se la ritenuta d'acconto del 20% è già stata applicata.
- I dati restano solo in locale in `extra.json` (ignorato da git).
- Le ritenute versate entrano tra le tasse pagate nell'anno (scheda Tasse & INPS).
- Stima del saldo al 730: IRPEF con scaglioni 2026 (23% / 33% / 43%) meno detrazione da lavoro dipendente, calcolata sulla differenza tra reddito da lavoro (stimato dalle buste paga o inserito a mano) con e senza il compenso, più addizionali, meno ritenute. È una stima indicativa: non considera altre detrazioni, bonus e contributo INPS Gestione separata.
- Metodo ritenuta: «20% del netto inserito» (default) oppure «20% del lordo» (netto ÷ 0,80, come da normativa).

## Temi grafici
Dal selettore in alto a destra si sceglie tra **Tema sobrio** (chiaro/scuro automatico, predefinito) e **Tema futuristico** (neon su sfondo scuro). La scelta resta salvata nel browser.
