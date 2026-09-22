# AI English Tutor

Applicazione web locale per esercitarsi sulla grammatica inglese A1 con
spiegazioni editoriali e pratica generata da un modello linguistico. Il
percorso contiene 36 unità ordinate, corregge sei domande per lezione e avanza
con almeno 5 risposte corrette.

L'MVP risolve un problema preciso: offrire sessioni brevi, riprendibili e
verificabili senza introdurre account, servizi applicativi remoti o una
piattaforma didattica completa. Le lezioni e lo storico restano in un database
SQLite sul computer dell'utente.

## Funzionalità presenti

- percorso A1 sequenziale di 36 unità;
- una lezione attiva alla volta, salvata prima di essere mostrata;
- spiegazione Markdown curata, tre esempi e sei domande a scelta multipla;
- bozze delle risposte conservate nel browser;
- correzione deterministica, soglia 5/6 e risultati consultabili;
- scarto della lezione senza avanzamento;
- generazione tramite LiteLLM con massimo due chiamate in 60 secondi;
- storico locale e stime di costo note, parziali o non disponibili.

## Limiti osservati

- la revisione copre un campione reale per ciascuna unità, ma una futura
  generazione può comunque richiedere controllo didattico;
- il controllo dei contenuti non equivale a una certificazione di un docente;
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
Quella specifica prova non ha eseguito chiamate a un provider LLM.

## Architettura essenziale

- `app/static/`: interfaccia HTML, CSS e JavaScript senza build frontend;
- `app/main.py`: API FastAPI e distribuzione dei file statici;
- `app/service.py`: ciclo della lezione, stati e storico;
- `app/generation.py`: provider, retry, tentativi persistenti e costi;
- `app/assessment.py`: correzione e avanzamento deterministici;
- `app/course.py`: contenuti verificati del percorso A1;
- `app/database.py`: schema e connessione SQLite;
- `app/data/grammar_explanations/`: le 36 spiegazioni Markdown curate;
- `app/data/sample_practice.json`: pratica di esempio usata soltanto nei test;
- `app/data/curriculum.json`: ordine, titoli e obiettivi delle unità;
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
LLM_MODEL=deepseek/deepseek-flash
LLM_API_KEY=replace-me
LLM_API_BASE=
DATABASE_PATH=data/tutor.db
```

Il prefisso `deepseek/` indica a LiteLLM il provider da chiamare. `LLM_API_BASE`
resta vuoto perché LiteLLM conosce già l'endpoint ufficiale di DeepSeek. È
supportato un solo provider/modello alla volta.

Senza `LLM_MODEL` o `LLM_API_KEY` l'app si avvia comunque: storico, risultati e
lezioni già salvate restano disponibili, mentre la home spiega perché non può
creare una nuova lezione.

## Avvio

```bash
make
```

Aprire <http://127.0.0.1:8000>. La documentazione interattiva delle API è su
<http://127.0.0.1:8000/docs>. L'ascolto su `127.0.0.1` mantiene l'app accessibile
soltanto dal computer locale.

Il `Makefile` carica `.env`, usa le dipendenze bloccate nel lockfile e limita
l'ascolto a `127.0.0.1`.

## Test

```bash
uv run --frozen pytest
```

I test non richiedono credenziali e non chiamano provider reali. Coprono schema,
curriculum, spiegazioni Markdown, renderer sicuro, snapshot storici,
compatibilità con il testo semplice, correzione, persistenza, API, retry,
timeout e contabilità tramite risposte simulate e tariffe deterministiche.

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

### Modificare una spiegazione

Ogni unità ha un file `app/data/grammar_explanations/A1-NN.md`, dove `A1-NN`
deve corrispondere a un ID presente nel curriculum. Il file non ripete titolo,
obiettivo o fonti e usa questa struttura:

```md
### Quando si usa

Testo introduttivo.

### Come si forma

- Regola essenziale.

### Attenzione

> Limite o contrasto importante.

### Errori comuni

- Errore plausibile e correzione.
```

Il renderer supporta soltanto paragrafi, titoli `###`, elenchi puntati,
citazioni, `**grassetto**` e `` `codice inline` ``. HTML, immagini, link e altra
sintassi vengono mostrati come testo inerte. Dopo una modifica eseguire
`uv run --frozen pytest`: i test controllano corrispondenza con il curriculum,
sezioni obbligatorie e costrutti esclusi. Le lezioni già salvate conservano la
propria copia e non vengono riscritte.

## AI e logica deterministica

L'AI viene chiamata soltanto quando si avvia una nuova lezione. Riceve livello,
identificativo, titolo, obiettivo e spiegazione Markdown verificata dell'unità,
oltre alle lingue richieste e allo schema JSON. Non riceve lo storico, le
risposte dell'utente o le lezioni precedenti. Il provider produce soltanto tre
esempi e sei esercizi con soluzioni e motivazioni; non può restituire o
sostituire ID e spiegazione. Il backend valida la pratica con Pydantic, la
unisce ai contenuti curati e salva lo snapshot completo.

Correzione, punteggio, soglia 5/6, avanzamento, scarto, storico e consultazione
dei risultati sono logica locale deterministica e non fanno altre richieste AI.
Il comportamento previsto è definito nella [specifica dell'MVP](docs/specs/MVP-SPEC.md).

## Dati locali e backup

- la chiave API resta nel processo backend e non viene inviata al browser;
- lezioni, soluzioni, risposte inviate, risultati e stime di costo sono in
  `DATABASE_PATH`, per impostazione predefinita `data/tutor.db`;
- le sole selezioni non ancora inviate sono nel `localStorage` del browser;
- l'app non include account, analytics, sincronizzazione o backup automatici;
- il provider LLM tratta il prompt descritto sopra secondo i propri termini e
  le proprie regole di conservazione, da consultare prima dell'uso.

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

DeepSeek `deepseek-flash` è stato collaudato il 22 settembre 2026 con LiteLLM
1.101.0. La prova end-to-end ha verificato autenticazione, JSON Output, schema,
consumi, costo, latenza, persistenza e operazioni offline. Un campione reale per
ciascuna delle 36 unità è stato revisionato; sei output iniziali hanno portato a
stringere il prompt e sono stati rigenerati con esito positivo. Quella prova
precede la separazione delle spiegazioni dal payload AI; l'attuale contratto
“pratica soltanto” è verificato dalla suite automatica senza una nuova chiamata
esterna.

Il [report completo del collaudo](MVP-VALIDATION.md) contiene misure, prezzi
ufficiali, problemi trovati, correzioni, checklist della specifica e limiti. Il
collaudo riguarda soltanto DeepSeek; non dichiara verificati altri provider.

## Risoluzione dei problemi

**La home non consente di iniziare una lezione.** Verificare che `.env` contenga
sia `LLM_MODEL` sia `LLM_API_KEY`, quindi riavviare con `make`.

**Il provider rifiuta credenziali o modello.** Controllare i nomi e la chiave
nella documentazione del provider scelto. L'app non prova automaticamente un
provider alternativo.

**DeepSeek risponde “Insufficient Balance”.** Aggiungere credito o verificare il
limite di spesa nell'account del provider, quindi riprovare. L'app non ritenta
automaticamente questo errore.

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
