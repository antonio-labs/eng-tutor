# AI English Tutor — Specifica MVP

**Stato: MVP completato e verificato il 22 settembre 2026**, con evidenze in [MVP-VALIDATION.md](MVP-VALIDATION.md). La specifica è allineata alle decisioni D01–D21 di [MVP-GRILLING.md](MVP-GRILLING.md) e al piano completato delle [spiegazioni grammaticali](GRAMMAR-EXPLANATIONS-PLAN.md). Attività in [tasks.md](tasks.md); programma e fonti in [A1-CURRICULUM.md](A1-CURRICULUM.md). Il [documento originale](ai-english-tutor-mvp-spec.md) resta la visione estesa: per la prima implementazione prevale questa spec.

## 1. Obiettivo e confini

Creare un tutor di grammatica inglese da usare personalmente e presentare su GitHub con documentazione precisa. Il ciclo centrale è: ricevere una lezione, esercitarsi, capire le soluzioni, salvare il risultato e proseguire lungo il curriculum. L'autore valuterà personalmente utilità e correttezza didattica attraverso i propri test.

Applicazione web locale per un solo studente, senza account. Livello A1 fisso; interfaccia e spiegazioni in italiano, esempi ed esercizi in inglese. L'MVP copre tutte le unità di grammatica A1 dell'inventario didattico documentato nella ricerca, non soltanto i cinque argomenti della prima bozza.

La copertura è **grammaticale**: il completamento del percorso non certifica il livello CEFR A1 e non valuta conversazione, ascolto o scrittura libera. La distinzione tra descrittori CEFR e inventario grammaticale è documentata nelle [fonti del curriculum](A1-CURRICULUM.md).

## 2. Lezione e durata

Ogni lezione tratta una sola unità del curriculum e contiene:

- Una spiegazione editoriale in italiano, versionata nel backend come Markdown.
- Tre esempi in inglese con brevi note in italiano.
- Sei esercizi a scelta multipla, ciascuno con tre opzioni distinte e una sola soluzione valida.
- Una motivazione della soluzione per ciascun esercizio, visibile dopo l'invio.

Il backend assegna un budget didattico A1 fisso: **3 minuti** per spiegazione ed esempi, **9 minuti** per gli esercizi (1,5 ciascuno), **3 minuti** per correzione e revisione. La somma è sempre **15 minuti stimati**; i pesi iniziali verranno valutati nei test manuali. Nessun timer obbligatorio, attesa imposta o esercizio aggiunto automaticamente quando l'utente termina prima.

## 3. Esperienza utente

Tre viste semplici, anche nella stessa pagina:

1. **Home:** prossimo argomento, unità superate sul totale del curriculum, «Inizia» oppure «Riprendi» e uno storico essenziale. Lo storico elenca lezioni completate e scartate con data, argomento, stato, punteggio quando presente e costo stimato; permette di riaprire i risultati delle lezioni completate. Nessun filtro o grafico.
2. **Lezione:** spiegazione, esempi e tutti gli esercizi nella stessa pagina. L'utente seleziona tutte le risposte prima dell'invio; può scartare la lezione finché non l'ha inviata.
3. **Risultato:** corrette su sei, percentuale, risposta scelta, soluzione e motivazione per ciascun esercizio, costo della generazione. Il prossimo avvio passa all'unità successiva oppure ripete quella non superata.

«Scarta lezione» libera la lezione attiva senza voto o avanzamento e conserva il costo già sostenuto. La nuova generazione richiede un nuovo clic su «Inizia»; non parte automaticamente.

Dopo l'ultima unità superata, mostrare «Percorso di grammatica A1 completato» e lasciare consultabile lo storico. Niente passaggio ad A2 o ripasso libero dei temi già superati nell'MVP.

## 4. Curriculum, valutazione e storico

Il curriculum ordinato è definito in [A1-CURRICULUM.md](A1-CURRICULUM.md) e sarà tradotto in un unico file JSON versionato. Ogni unità ha identificativo stabile, titolo e obiettivo; la posizione nell'elenco determina l'ordine. Il modello non sceglie argomenti, livello o progressione.

- Proporre la prima unità non ancora superata; una lezione attiva ha precedenza sulla nuova generazione.
- Punteggio: `corrette / 6 × 100`, arrotondato all'intero solo per la visualizzazione.
- Superamento: almeno cinque risposte corrette su sei. Quattro danno 67% e richiedono un nuovo tentativo; cinque danno 83% e consentono di avanzare.
- Un risultato completato rimane immutabile. I tentativi non superati restano nello storico; il tentativo successivo genera nuovi contenuti per la stessa unità.
- Progressi derivati dai risultati completati: nessun profilo separato, nessuna memoria di errori specifici, nessuna classificazione delle debolezze o personalizzazione del prompt in base agli errori.

Le risposte originali vengono salvate per riaprire il risultato, senza trasformarle in un modello delle difficoltà dello studente. Il numero totale di unità nell'interfaccia è ricavato dal curriculum, non scritto a mano nel codice.

## 5. Generazione AI e client agnostico

Una richiesta genera soltanto la pratica: tre esempi e sei esercizi, comprese le
motivazioni delle soluzioni. Il backend carica la spiegazione Markdown verificata
per l'unità, la invia come contesto autorevole insieme a livello, titolo,
obiettivo, lingue e formato fisso, poi assembla il `LessonContent`. Non invia
storico o risposte dello studente. Nessuna richiesta AI per spiegazione,
correzione, punteggio o scelta del prossimo argomento.

Usare **LiteLLM Python SDK** direttamente come client comune, con un solo provider/modello attivo e configurazione sul backend: `LLM_MODEL`, `LLM_API_KEY` ed eventuale `LLM_API_BASE`. La sua interfaccia comune evita di implementare adattatori nel progetto; non serve avviare il suo gateway o router. La compatibilità riguarda i provider supportati dal client, con i requisiti di autenticazione del servizio scelto. [Documentazione LiteLLM](https://docs.litellm.ai/docs/).

Durante lo sviluppo il provider è stato rinviato e i test hanno usato risposte
simulate; il collaudo finale ha verificato DeepSeek `deepseek-flash`, come
documentato in [MVP-VALIDATION.md](MVP-VALIDATION.md). Senza configurazione,
l'app deve comunque mostrare storico e lezioni già salvate e spiegare perché non
può crearne di nuove.

Il generatore richiede JSON con soli esempi ed esercizi; `unit_id` e
`explanation` non fanno parte dello schema controllato dal provider. Ogni
esercizio contiene identificativo, domanda, opzioni, indice della soluzione e
motivazione. Il backend valida sempre i dati con Pydantic: testi non vuoti,
quantità previste, ID univoci, tre opzioni distinte e indice valido. Il formato
strutturato nativo si usa quando supportato dal modello; la compatibilità del
client non garantisce le medesime capacità di output per ogni provider. [Output
strutturati LiteLLM](https://docs.litellm.ai/docs/completion/json_mode).

Il prompt richiede contenuti pertinenti all'obiettivo, lessico semplice, domande non duplicate e una sola soluzione valida. La validazione dello schema non dimostra la correttezza grammaticale: l'autore controllerà manualmente un campione per ogni unità.

Generazione e nuovo tentativo hanno un limite complessivo di **60 secondi**, con **al massimo due chiamate**. Il secondo tentativo avviene solo per un errore recuperabile o contenuto non valido, se resta tempo; errori di configurazione e credenziali si mostrano subito. Evitare tentativi nascosti aggiunti dal client. Alla scadenza, mostrare un errore recuperabile senza perdere progressi o presentare contenuti parziali. Impedire avvii duplicati mentre una generazione è in corso.

## 6. Costi

Mostrare il **costo stimato in USD** di ogni lezione creata, senza imporre un tetto di spesa applicativo. Timeout e limite dei tentativi restano attivi. Non promettere assenza di limiti imposti dal provider.

Registrare ogni chiamata con modello, consumi restituiti quando disponibili, esito, importo stimato e riferimento/versione delle tariffe utilizzate. Usare le funzioni del client per la stima, verificandone i risultati sul modello scelto; documentare la fonte dei prezzi. [Consumi e costi LiteLLM](https://docs.litellm.ai/docs/completion/token_usage).

- Il costo della lezione include tutti i tentativi della relativa generazione, anche output respinti prima di quello valido.
- Riaprire, inviare, correggere e consultare una lezione non genera costi AI aggiuntivi.
- Scartare una lezione non cancella le spese sostenute.
- Se consumi o tariffe non sono disponibili, indicare «non disponibile»; se sono noti solo alcuni tentativi, mostrare il subtotale come «parziale». Non sostituire un costo sconosciuto con zero.
- Se la generazione termina senza una lezione, conservare i tentativi e mostrare nell'errore gli eventuali costi noti o la loro indisponibilità. Non creare un risultato didattico fittizio.
- Salvare la stima al momento della chiamata: cambiare provider o aggiornare le tariffe non riscrive i costi storici. La stima non è la fattura del provider.

## 7. Salvataggio e architettura

Un processo Python con FastAPI/Pydantic, HTML/CSS/JavaScript serviti dallo stesso backend e SQLite tramite la libreria standard. Curriculum in JSON; nessun agente, LangGraph, servizio separato o database vettoriale.

Due tabelle sono sufficienti:

- `lessons`: identificativo, unità, contenuto completo in JSON, stato (`active`, `completed`, `discarded`), risposte inviate, numero di risposte corrette e date. Una sola lezione attiva alla volta.
- `generation_calls`: identificativo, gruppo di generazione, eventuale lezione associata, modello/provider, esito, consumi, costo stimato quando noto, riferimento tariffario e data. Serve anche per chiamate che non producono una lezione; non è un servizio di contabilità separato.

Salvare la lezione prima di mostrarla, inclusa una copia della spiegazione
editoriale: modificare in seguito il file Markdown non riscrive lo storico. Al
browser arrivano solo i contenuti didattici pubblici: soluzioni e motivazioni
restano sul backend fino all'invio; anche il recupero di una lezione attiva o
scartata le esclude. Il testo semplice presente in vecchi record resta valido.

Ricaricamento e riavvio recuperano la stessa lezione. Le selezioni provvisorie sono salvate nel browser per ID della lezione e cancellate dopo invio riuscito o scarto. Il backend verifica completezza, ID e opzioni contro la lezione salvata; salva risposte, punteggio e completamento insieme. Un invio ripetuto restituisce il risultato già salvato. Una lezione scartata non può essere inviata; una completata non può essere scartata. Errori di salvataggio permettono di riprovare senza perdere le risposte.

L'app ascolta solo sull'interfaccia locale. Chiavi API e database non entrano nel
controllo versione; le chiavi non vengono inviate al browser o stampate nei log.
Soltanto la spiegazione usa un renderer Markdown che costruisce nodi DOM tramite
`textContent` e supporta paragrafi, titoli `###`, elenchi puntati, citazioni,
grassetto e codice inline. HTML, immagini, link e sintassi non supportata restano
testo inerte; tutti gli altri contenuti sono mostrati come testo. Controlli
accessibili da tastiera, etichette chiare, stati di caricamento e feedback non
basato soltanto sul colore.

Lezioni salvate, correzione e storico funzionano senza connessione; la generazione richiede il provider. Documentare la copia manuale del database ad app ferma; nessun backup automatico o sincronizzazione.

## 8. Criteri di completamento e documentazione

- [x] Tutte le unità del curriculum A1 documentato sono presenti nel JSON, nell'ordine previsto e con obiettivi verificabili.
- [x] Tutte le 36 unità hanno una spiegazione Markdown editoriale revisionata, strutturalmente verificata e salvata come snapshot nella lezione.
- [x] Il flusso completo funziona: inizio/ripresa, lezione, invio, correzione, storico, avanzamento e conclusione.
- [x] Ogni lezione contiene il formato previsto e riporta 15 minuti stimati, senza obbligare l'utente ad aspettare.
- [x] Punteggi, invii non validi/duplicati, scarto e ripartenza rispettano le regole sopra; soluzioni non esposte prima dell'invio.
- [x] Progressi e lezioni sopravvivono al riavvio; errori del provider e del salvataggio non li alterano.
- [x] Client agnostico configurabile, massimo due chiamate e 60 secondi complessivi; test automatici senza credenziali o chiamate a pagamento.
- [x] Costi salvati e visibili, inclusi nuovi tentativi e lezioni scartate; valori mancanti e parziali sono espliciti.
- [x] Dopo la scelta del provider: prova reale di generazione, formato, consumi, tariffe e tempi. Finché manca, indicare il collaudo reale come non eseguito.
- [x] L'autore controlla manualmente un campione di lezioni per ogni unità e documenta problemi e limiti osservati.
- [x] README con scopo, demo del comportamento reale, prerequisiti, avvio, configurazione, test, architettura essenziale, fonti del curriculum, limiti e roadmap; esempio di configurazione senza segreti.

La documentazione deve distinguere funzionalità implementate, test realmente eseguiti e sviluppi futuri. Il giudizio sull'utilità rimane all'autore, senza metriche di adozione obbligatorie o autovalutazione del prodotto.

## 9. Sviluppi successivi

Fuori dall'MVP: A2 e scelta del livello, altri tipi di esercizi, sessioni da 30 minuti, memoria di errori specifici, adattamento dei contenuti, più lezioni per unità e ripasso dei temi già superati. Il dataset di esercizi divisi per livello ed eventuale RAG verranno progettati separatamente.

Rimangono futuri anche account, più dispositivi, pubblicazione online, voce, chat, vocabolario, lettura, scrittura libera, livelli superiori, gamification e pagamenti. Nuovi agenti o infrastruttura saranno valutati solo se richiesti da una funzionalità concreta. Nessun codice preparatorio per queste evoluzioni.
