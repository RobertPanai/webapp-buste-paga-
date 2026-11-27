# PAYSLIP//CORE

Dashboard locale per leggere e consultare le buste paga Terna in PDF (formato **Prospetto Paga**). L'applicazione gira sul tuo computer e si apre nel browser all'indirizzo `127.0.0.1`.

## Installazione

Servono Git e Python 3.10 o successivo. Da Terminale:

```sh
git clone https://github.com/RobertPanai/webapp-buste-paga-.git
cd webapp-buste-paga-
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

La cartella `.venv` contiene l'ambiente Python dedicato al progetto. Il comando `pip install -r requirements.txt` installa le dipendenze necessarie; non occorre installare altro.

## Avvio rapido

Crea sul computer una cartella privata per i PDF, per esempio `$HOME/buste-paga-pdf`, e copia lì i tuoi cedolini. Non caricare PDF, estratti conto o altri dati personali su GitHub: per usare la dashboard basta che i file si trovino in una cartella locale leggibile dal tuo utente.

Dalla cartella del progetto avvia:

```sh
BUSTE_DIR="$HOME/buste-paga-pdf" ./buste_paga
```

Apri quindi <http://127.0.0.1:8765>. Il programma cerca ricorsivamente i PDF nella cartella indicata. In alternativa, puoi avviare `./buste_paga` senza `BUSTE_DIR`: in quel caso la cartella del progetto è usata come cartella dei PDF. Puoi cambiare cartella anche dal pulsante **Cartella** nella dashboard; la scelta viene salvata localmente in `config.json`.

Il launcher usa `.venv/bin/python` se hai creato l'ambiente seguendo i passaggi sopra. Per avviare manualmente il server, attiva prima l'ambiente e usa `BUSTE_DIR="$HOME/buste-paga-pdf" python server.py`; resta aperto nel Terminale finché la dashboard è in uso. Per fermarlo premi `Ctrl+C`.

### Comando facoltativo `buste_paga` su macOS/zsh

Per avviare il progetto senza entrare ogni volta nella sua cartella, aggiungi un alias a `~/.zshrc`. Sostituisci `/percorso/del/progetto` con il percorso effettivo della cartella clonata e scegli una cartella privata per i PDF:

```sh
alias buste_paga='BUSTE_DIR="$HOME/buste-paga-pdf" "/percorso/del/progetto/buste_paga"'
```

Ricarica la configurazione con `source ~/.zshrc`. Da quel momento puoi eseguire `buste_paga` in un Terminale. Puoi cambiare la cartella dei PDF anche dal pulsante **Cartella**.

## Uso della dashboard

- **Buste paga:** la dashboard legge PDF in formato Terna **Prospetto Paga**. I file nuovi o modificati vengono analizzati e i risultati sono conservati in `cache.json` per velocizzare gli avvii successivi; la scansione si aggiorna automaticamente. **Rileggi tutto** ricostruisce la cache.
- **Panoramica annuale:** per l'anno selezionato mostra il netto medio per cedolino, gli altri redditi effettivamente incassati divisi per cedolino e il netto medio combinato. Il denominatore è il numero di cedolini utilizzabili dell'anno: vengono inclusi tutti i cedolini distinti, anche quelli aggiuntivi dello stesso mese; copie identiche del medesimo PDF sono conteggiate una volta. Se sostituisci un PDF con una copia diversa, elimina anche il vecchio file dalla cartella per evitare che entrambi siano conteggiati. Gli altri redditi non incassati non entrano nella media.
- **Controlli:** nel dettaglio di ogni busta sono confrontate le somme di competenze, trattenute e netto con i totali indicati nel PDF.
- **Altri redditi:** puoi registrare compensi fuori busta paga e indicare se sono incassati e se è stata applicata la ritenuta. I dati sono salvati in locale in `extra.json`. La scheda presenta una stima indicativa del 730.
- **Temi:** il selettore in alto permette di scegliere il tema **sobrio** (predefinito, con modalità chiara/scura automatica) o **futuristico**. La scelta resta salvata nel browser.

## Home banking facoltativo

Apri **Cartella** e attiva **Analizza anche l'home banking**. Puoi mettere gli estratti conto `.xls` o `.xlsx` nella cartella `home_banking` dentro quella dei PDF, oppure caricarli dalla scheda **Banca** con **Carica file**. L'upload salva una copia con la data di caricamento nel nome; l'app evita di duplicare i movimenti comuni a estratti sovrapposti.

I dati degli estratti conto restano in uso locale. I file Excel, la cache bancaria e le cartelle dati sono esclusi dal repository tramite `.gitignore`: non inserirli né committarli su GitHub.

## Arresto, riavvio e problemi comuni

- **La porta 8765 è già in uso:** ferma l'altra istanza della dashboard con `Ctrl+C` nel Terminale in cui è avviata. Se non riesci a fermarla, avvia un'altra istanza su una porta diversa: con l'ambiente attivato esegui `BUSTE_DIR="$HOME/buste-paga-pdf" python server.py 8766` e apri <http://127.0.0.1:8766>. Il launcher `./buste_paga` usa la porta predefinita 8765.
- **Hai aggiornato il codice:** ferma e riavvia il server; la pagina da sola non riavvia il processo Python. Se i risultati non riflettono modifiche ai PDF, usa **Rileggi tutto**.
- **Nessuna busta trovata:** controlla il percorso mostrato in alto e verifica che contenga PDF Prospetto Paga. Se necessario, seleziona la cartella corretta con **Cartella**.
- **Dipendenza mancante:** dalla cartella del progetto attiva `.venv` con `source .venv/bin/activate` e ripeti `python -m pip install -r requirements.txt`.

## Dati locali e repository

PDF, configurazione, cache, altri redditi ed estratti conto sono dati personali e devono restare sul tuo computer. Non serve copiare i cedolini nel repository né inviarli su GitHub. Le regole `.gitignore` escludono i principali file dati locali; prima di condividere modifiche al codice controlla comunque `git status` e assicurati che non siano stati aggiunti dati personali.
