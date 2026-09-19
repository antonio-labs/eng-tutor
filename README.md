# AI English Tutor

Applicazione web locale per esercitarsi sulla grammatica inglese A1 con lezioni
generate da un modello linguistico. Il percorso contiene 36 unità ordinate,
corregge sei domande per lezione e avanza con almeno 5 risposte corrette.

L'MVP risolve un problema preciso: offrire sessioni brevi, riprendibili e
verificabili senza introdurre account, servizi applicativi remoti o una
piattaforma didattica completa. Le lezioni e lo storico restano in un database
SQLite sul computer dell'utente.

## Cosa include

- percorso A1 sequenziale di 36 unità;
- una lezione attiva alla volta, salvata prima di essere mostrata;
- spiegazione, tre esempi e sei domande a scelta multipla;
- bozze delle risposte conservate nel browser;
- correzione deterministica, soglia 5/6 e risultati consultabili;
- scarto della lezione senza avanzamento;
- generazione tramite LiteLLM con massimo due chiamate in 60 secondi;
- storico locale e stime di costo note, parziali o non disponibili.

Non include autenticazione, sincronizzazione tra dispositivi, deployment,
certificazione linguistica o adattamento personalizzato del percorso.

## Flusso utente

1. La home mostra la prossima unità e il progresso complessivo.
2. **Inizia** genera e salva la lezione; **Riprendi** riapre quella attiva.
3. Le risposte selezionate restano nel browser anche dopo un ricaricamento.
4. **Invia risposte** corregge i sei esercizi senza una nuova chiamata AI.
5. Il risultato mostra punteggio, soluzioni, motivazioni e costo disponibile.
6. Con almeno 5/6 la home passa all'unità successiva; altrimenti ripropone la
   stessa unità in una nuova lezione.

## Architettura essenziale

- `app/static/`: interfaccia HTML, CSS e JavaScript senza build frontend;
- `app/main.py`: API FastAPI e distribuzione dei file statici;
- `app/service.py`: ciclo della lezione, stati, retry e aggregazione dei costi;
- `app/generation.py`: singolo client LiteLLM e validazione dell'output;
- `app/grading.py`: correzione e avanzamento deterministici;
- `app/database.py`: schema e connessione SQLite;
- `app/data/`: curriculum e lezione di esempio usata soltanto nei test;
- `tests/`: test unitari e di integrazione con chiamata LLM sostituita da mock.

## Prerequisiti

- macOS o Linux;
- [uv](https://docs.astral.sh/uv/);
- Python 3.12, installabile automaticamente da `uv`.

Non serve una API key per installare il progetto, consultare dati già salvati o
eseguire i test. Serve una configurazione LLM valida soltanto per generare una
nuova lezione.

## Installazione

```bash
git clone <URL_DEL_REPOSITORY>
cd ai-eng-tutor
uv sync --frozen
cp .env.example .env
```

Il lockfile fissa tutte le dipendenze. `.env` e il database locale sono esclusi
da Git.

## Configurazione

Modificare `.env` senza inserire mai credenziali nei file versionati:

```dotenv
LLM_MODEL=provider/model-name
LLM_API_KEY=replace-me
LLM_API_BASE=
DATABASE_PATH=data/tutor.db
```

`LLM_MODEL` usa il nome accettato da LiteLLM. `LLM_API_BASE` è opzionale e va
impostato solo se il provider richiede un endpoint personalizzato. È supportato
un solo provider/modello alla volta.

Senza `LLM_MODEL` o `LLM_API_KEY` l'app si avvia comunque: storico, risultati e
lezioni già salvate restano disponibili, mentre la home spiega perché non può
creare una nuova lezione.

## Avvio

```bash
uv run --frozen --env-file .env uvicorn app.main:app \
  --host 127.0.0.1 --port 8000
```

Aprire <http://127.0.0.1:8000>. La documentazione interattiva delle API è su
<http://127.0.0.1:8000/docs>. L'ascolto su `127.0.0.1` mantiene l'app accessibile
soltanto dal computer locale.

Durante lo sviluppo si può aggiungere `--reload` al comando di avvio.

## Test

```bash
uv run --frozen pytest
```

I test non richiedono credenziali e non chiamano provider reali. Coprono schema,
curriculum, correzione, persistenza, API, retry, timeout e contabilità tramite
risposte simulate e tariffe deterministiche.

## Risoluzione dei problemi

**La home non consente di iniziare una lezione.** Verificare che `.env` contenga
sia `LLM_MODEL` sia `LLM_API_KEY` e che l'avvio includa `--env-file .env`.

**Il provider rifiuta credenziali o modello.** Controllare i nomi e la chiave
nella documentazione del provider scelto. L'app non prova automaticamente un
provider alternativo.

**La generazione scade o fallisce due volte.** Ogni operazione dispone al massimo
di 60 secondi complessivi e due chiamate. Il tentativo viene registrato; si può
riprovare dalla home.

**Il costo è “non disponibile”.** Il provider o LiteLLM non hanno restituito
consumi o una tariffa riconosciuta. L'etichetta non significa che la chiamata sia
gratuita.

**SQLite segnala che il database è occupato.** Chiudere eventuali altri processi
dell'app che usano lo stesso `DATABASE_PATH`, quindi riprovare.

**Serve ripartire con un database vuoto.** Arrestare l'app e spostare il file in
una posizione di backup, per esempio `mv data/tutor.db data/tutor.backup.db`,
quindi riavviare. Il database verrà ricreato automaticamente.
