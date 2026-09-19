# AI English Tutor

Applicazione web locale per esercitarsi sulla grammatica inglese A1 con lezioni
generate da un modello linguistico. Il percorso contiene 36 unità ordinate,
corregge sei domande per lezione e avanza con almeno 5 risposte corrette.

L'MVP risolve un problema preciso: offrire sessioni brevi, riprendibili e
verificabili senza introdurre account, servizi applicativi remoti o una
piattaforma didattica completa. Le lezioni e lo storico restano in un database
SQLite sul computer dell'utente.

## Funzionalità presenti

- percorso A1 sequenziale di 36 unità;
- una lezione attiva alla volta, salvata prima di essere mostrata;
- spiegazione, tre esempi e sei domande a scelta multipla;
- bozze delle risposte conservate nel browser;
- correzione deterministica, soglia 5/6 e risultati consultabili;
- scarto della lezione senza avanzamento;
- generazione tramite LiteLLM con massimo due chiamate in 60 secondi;
- storico locale e stime di costo note, parziali o non disponibili.

## Limiti osservati

- il provider e il modello non sono ancora stati scelti o collaudati dal vivo;
- la validazione strutturale non garantisce da sola la correttezza didattica del
  testo generato, che richiede la revisione prevista nel blocco 5;
- il percorso copre la grammatica A1, non tutte le competenze CEFR A1;
- dati e bozze sono locali al computer e al browser, senza sincronizzazione;
- le stime di costo possono essere parziali o non disponibili;
- non sono inclusi account, deployment o adattamento personale del percorso.

## Roadmap fuori dall'MVP

Memoria degli errori ricorrenti, dataset didattico o RAG, più lezioni per lo
stesso argomento e ripassi programmati restano sviluppi futuri. Non esistono
componenti vuoti o astrazioni predisposte per queste funzioni nella versione
attuale.

## Flusso utente

1. La home mostra la prossima unità e il progresso complessivo.
2. **Inizia** genera e salva la lezione; **Riprendi** riapre quella attiva.
3. Le risposte selezionate restano nel browser anche dopo un ricaricamento.
4. **Invia risposte** corregge i sei esercizi senza una nuova chiamata AI.
5. Il risultato mostra punteggio, soluzioni, motivazioni e costo disponibile.
6. Con almeno 5/6 la home passa all'unità successiva; altrimenti ripropone la
   stessa unità in una nuova lezione.

## Esempio del flusso verificato

Questa sequenza è stata eseguita il 19 settembre 2026 nell'app funzionante, con
un database temporaneo e la lezione di esempio dichiarata come simulata:

1. la home mostrava **Pronomi soggetto e presente di be** e progresso `0/36`;
2. dopo **Inizia**, la pagina mostrava spiegazione, tre esempi e sei domande;
3. alcune risposte sono state selezionate e un ricaricamento le ha ripristinate;
4. l'invio completo, anche con doppio clic, ha prodotto una sola volta il
   risultato `6/6`, `100%`, **Lezione superata**;
5. la home è passata a `1/36` e all'unità **Negazioni e domande con be**;
6. la nuova lezione è stata ripresa dopo un ricaricamento, poi scartata senza
   avanzare; lo storico ha mantenuto sia il risultato precedente sia lo scarto;
7. **Apri risultato** ha riaperto il dettaglio immutato della prima lezione.

Con un secondo database di prova già completato, la home ha mostrato `36/36` e
**Percorso di grammatica A1 completato**. La stessa prova ha verificato uso da
tastiera, modalità scura e assenza di interpretazione HTML dei testi mostrati.
Non è stata eseguita alcuna chiamata a un provider LLM.

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

## Contenuti, fonti e durata

Il [curriculum completo e la tabella di copertura](A1-CURRICULUM.md) documentano
le 36 unità e le fonti usate per ciascun argomento. Il perimetro deriva dal
[British Council–EAQUALS Core Inventory for General English](https://www.teachingenglish.org.uk/sites/teacheng/files/pub-british-council-eaquals-core-inventoryv2.pdf),
con riscontri nelle risorse British Council e Cambridge collegate nel curriculum.
Il [CEFR del Consiglio d'Europa](https://www.coe.int/en/web/common-european-framework-reference-languages/table-3-cefr-3.3-common-reference-levels-qualitative-aspects-of-spoken-language-use)
descrive competenze comunicative più ampie: completare questo percorso di sola
grammatica non certifica il raggiungimento del livello A1.

Ogni lezione riporta **15 minuti stimati**: 3 per spiegazione ed esempi, 9 per i
sei esercizi e 3 per correzione e revisione. È un budget didattico assegnato dal
backend, non un timer né una misura del tempo reale. Le 36 unità corrispondono a
540 minuti nominali, esclusi i tentativi ripetuti.

## AI e logica deterministica

L'AI viene chiamata soltanto quando si avvia una nuova lezione. Riceve livello,
identificativo, titolo e obiettivo dell'unità, lingue richieste e schema JSON;
non riceve lo storico, le risposte dell'utente o le lezioni precedenti. Il
provider produce spiegazione, esempi, domande, soluzioni e motivazioni, poi il
backend valida tutto con Pydantic prima del salvataggio.

Correzione, punteggio, soglia 5/6, avanzamento, scarto, storico e consultazione
dei risultati sono logica locale deterministica e non fanno altre richieste AI.
Il comportamento previsto è definito nella [specifica dell'MVP](MVP-SPEC.md).

## Dati locali e backup

- la chiave API resta nel processo backend e non viene inviata al browser;
- lezioni, soluzioni, risposte inviate, risultati e stime di costo sono in
  `DATABASE_PATH`, per impostazione predefinita `data/tutor.db`;
- le sole selezioni non ancora inviate sono nel `localStorage` del browser;
- l'app non include account, analytics, sincronizzazione o backup automatici;
- il provider LLM tratta il prompt descritto sopra secondo i propri termini e
  le proprie regole di conservazione, da verificare prima del collaudo reale.

Per un backup manuale, arrestare l'app e copiare il database in una posizione
sicura, adattando i percorsi se `DATABASE_PATH` è diverso:

```bash
cp data/tutor.db /percorso/sicuro/tutor-backup.db
```

La copia conserva lezioni e storico, ma non le selezioni provvisorie presenti
soltanto nel browser.

## Costi

Per ogni chiamata l'app salva provider, modello, consumi disponibili, stima USD
e riferimento tariffario. La stima usa i dati restituiti da LiteLLM e la sua
[mappa dei costi dei modelli](https://docs.litellm.ai/docs/completion/token_usage).
Tutti i tentativi attribuiti alla stessa generazione concorrono al totale; i
consumi noti di generazioni fallite restano visibili separatamente.

La dicitura **parziale** indica che soltanto alcuni tentativi hanno un costo
noto; **non disponibile** indica che manca il consumo o il prezzo. Gli importi
vengono conservati come stimati al momento della chiamata e non sono aggiornati
quando cambiano le tariffe. Non equivalgono alla fattura del provider e l'app
non applica un limite di spesa: limiti, crediti e fatturazione vanno controllati
nel servizio scelto.

## Stato del collaudo LLM

Al 19 settembre 2026 non è stato scelto né chiamato un provider reale. Il client,
la validazione, i retry, gli errori, i consumi e i costi sono verificati con mock
deterministici; il flusso browser è stato provato con il contenuto di esempio.
Restano aperti autenticazione reale, capacità del modello, qualità didattica,
latenza, consumi e tariffa effettivi descritti nel blocco 5 di [tasks.md](tasks.md).

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
