# AI English Tutor — Decisioni e dubbi prima dello sviluppo

Traccia di una sessione di grilling basata su [MVP-SPEC.md](docs/specs/MVP-SPEC.md) e sulla [visione originale](docs/specs/ai-english-tutor-mvp-spec.md).

Lo scopo è capire che cosa vogliamo verificare, quali compromessi accettiamo e come gestire i casi concreti. Le risposte dell'autore a D01–D22 sono state registrate. Per ogni domanda, **la decisione dell'autore prevale sulla raccomandazione iniziale**; le decisioni successive aggiornano i punti delle risposte precedenti.

**Stato: chiarimenti conclusi per la pianificazione.** [MVP-SPEC.md](docs/specs/MVP-SPEC.md) contiene il perimetro allineato; [tasks.md](tasks.md) contiene le attività da sviluppare. Questo file conserva il ragionamento e le decisioni, non descrive funzionalità già implementate.

## Come usarlo

Le domande e le raccomandazioni iniziali restano come traccia della discussione. Per sviluppare seguire la spec allineata e le decisioni riportate sotto, senza riaprire automaticamente gli argomenti già risolti. L'utilità sarà giudicata personalmente dall'autore attraverso i propri test: non serve un sistema che la valuti automaticamente.

Non restano domande di prodotto bloccanti. La scelta del provider e del modello è rinviata intenzionalmente: lo sviluppo usa un client agnostico e test con risposte simulate; il collaudo reale verrà eseguito dopo la configurazione scelta dall'autore.

## Perimetro attuale

- MVP personale, locale e senza account, con curriculum di grammatica A1 completo rispetto all'inventario didattico scelto nella [ricerca](A1-CURRICULUM.md). Il precedente limite di cinque argomenti è superato; A1 resta l'unico livello disponibile.
- Ogni lezione contiene 18 esercizi in tre blocchi da sei e un budget didattico
  stimato di 15 minuti. Si avanza con almeno 15 risposte corrette; spiegazioni
  in italiano e contenuti di esercizio in inglese.
- Le lezioni sono generate dall'AI; punteggi e avanzamento sono calcolati dall'app. La motivazione della soluzione viene generata insieme all'esercizio.
- La soluzione prevista è un'app locale con Python/FastAPI, interfaccia semplice e SQLite. Nel progetto ci sono documenti, non ancora un'implementazione da verificare.
- A2, account, altri tipi di esercizi, chat, voce e personalizzazione avanzata sono rinviati. Non serve ridiscuterli senza un motivo concreto emerso dalle risposte.

## Decisioni confermate dalle risposte

- **Scopo:** progetto da mostrare sul profilo GitHub, con documentazione precisa; anche utilizzabile personalmente e potenzialmente trasformabile in prodotto.
- **Valutazione:** l'autore giudica utilità e risultati attraverso i propri test. Nessuna valutazione automatica dell'utilità dell'app e nessuna soglia obbligatoria di adozione del prodotto.
- **Avanzamento:** 15 risposte corrette su 18 e nessun salto di argomento. D22
  sostituisce il precedente formato da sei esercizi.
- **Recupero:** «Scarta lezione» prima dell'invio, senza voto o cambiamenti ai progressi; nuova generazione solo su richiesta.
- **Generazione:** client agnostico, un provider/modello configurato alla volta tramite API key; massimo 60 secondi complessivi e al massimo un tentativo automatico aggiuntivo. La scelta del provider è successiva e non blocca la pianificazione.
- **Costi:** conteggio per ogni lezione creata, senza un tetto di spesa imposto dall'app. Questo non elimina timeout e limite dei tentativi già accettati, né costituisce una promessa sui limiti del servizio esterno.
- **Uso e dati:** browser sul computer attuale; bozze nel browser, lezioni e risultati in SQLite, senza sincronizzazione o backup automatico.
- **Memoria:** salvare lo storico. Nessuna memoria di errori specifici o personalizzazione del contenuto in base agli errori nell'MVP.
- **Durata:** 15 minuti stimati dai contenuti, senza imporre un tempo reale minimo all'utente.
- **Controllo didattico:** l'autore verifica manualmente un campione di esercizi, soluzioni e spiegazioni durante i test.
- **Fine del percorso:** mantenere per ora la conclusione prevista. Più lezioni per argomento, ripassi e un dataset di esercizi per livello con eventuale RAG sono sviluppi futuri.

Per il progetto GitHub, la documentazione dovrà spiegare scopo e limiti reali, avvio riproducibile, configurazione senza segreti, flusso di una lezione, responsabilità dell'AI e della logica deterministica, test eseguibili, calcolo dei costi e sviluppi futuri. Non occorre moltiplicare i documenti o introdurre architettura solo per presentare il progetto.

## 1. Scopo e valore

### D01 — Qual è il risultato principale che vuoi ottenere da questo progetto?

**Domanda:** se dovessi scegliere un solo risultato, vorresti migliorare il tuo inglese oppure imparare a sviluppare applicazioni AI?

**Perché conta:** un tutor utile e un progetto formativo per lo sviluppatore hanno criteri di successo diversi. Per esempio, introdurre un framework ad agenti può essere un obiettivo di studio, ma non è richiesto dal flusso attuale.

**Risposta consigliata:** assumere come obiettivo principale un piccolo tutor funzionante; imparare sviluppo AI costruendolo. Se l'obiettivo principale è invece studiare una tecnologia specifica, nominarla esplicitamente prima di confermare le scelte tecniche.

**La tua decisione:** realizzare un progetto da mostrare sul profilo GitHub, con documentazione molto precisa. Deve poter essere usato anche personalmente e, in futuro, eventualmente diventare un prodotto vero e proprio. La documentazione è quindi parte del risultato da consegnare; la pubblicazione del repository non è un'azione richiesta in questa fase.

### D02 — Chi può verificare davvero che sia utile a un principiante?

**Domanda:** sarai tu a usarlo e il tuo livello è compatibile con questi cinque argomenti introduttivi?

**Perché conta:** una persona che conosce già gli argomenti può verificare che l'app funzioni, ma quella prova non dimostra che aiuti un principiante.

**Risposta consigliata:** usarlo personalmente per il primo test. Se gli argomenti sono già troppo facili, dichiarare che il test verifica il prodotto dal punto di vista funzionale; per valutarne l'utilità didattica servirà anche una prova con un principiante, possibile sullo stesso computer senza account aggiuntivi.

**La tua decisione:** per adesso valuterai personalmente se il progetto è utile. Non vuoi che sia il sistema a giudicare la propria utilità. Restano previsti correzione degli esercizi, punteggi e test del software: sono funzioni diverse dalla valutazione dell'utilità del prodotto.

### D03 — Quale fatica concreta dovrebbe toglierti?

**Domanda:** perché dovresti aprire questa app invece di chiedere una lezione a una chat AI o usare esercizi già disponibili?

**Perché conta:** generare testo non basta a definire il valore del prodotto. La risposta determina quali parti del flusso devono essere particolarmente semplici.

**Risposta consigliata:** il valore da verificare è «apro l'app e so subito cosa studiare; faccio gli esercizi, capisco le soluzioni e ritrovo il punto raggiunto». La generazione AI serve a variare gli esercizi nei nuovi tentativi; la sua utilità resta un'ipotesi da provare.

**La tua decisione:** «L'obiettivo è snellire e facilitare la creazione di esercizi precisi per l'utente, ricordarsi i punti da migliorare e non le possibili lezioni successive e quelle svolte. Come se fosse un professore a tua disposizione».

**Chiarito in D18:** per l'MVP salvare soltanto lo storico e mantenere l'avanzamento semplice. La memoria di errori specifici e gli esercizi mirati sono futuri; non viene aggiunta una chat.

### D04 — Quale prova ti farà dire che vale la pena continuare?

**Domanda:** al termine del primo periodo d'uso, quali osservazioni ti convinceranno a sviluppare la versione successiva?

**Perché conta:** «l'app funziona» è un criterio di completamento tecnico, non una prova di utilità o di apprendimento.

**Risposta consigliata:** provare cinque sessioni distribuite su più giorni, anche ripetendo argomenti. Annotare manualmente durata, punti di confusione e utilità del feedback. Considerare promettente il prodotto se almeno quattro sessioni si completano senza aiuto esterno e viene voglia di continuare. È un criterio iniziale da concordare, non una misura scientifica di apprendimento; non richiede analytics nell'app.

**La tua decisione:** deciderai personalmente sulla base dei tuoi test. Il protocollo proposto sopra, con cinque sessioni e una soglia di quattro completamenti, non diventa un requisito. I criteri tecnici di completamento restano verificabili; il giudizio di utilità è tuo.

## 2. Esperienza didattica

### D05 — Quale capacità stiamo effettivamente esercitando?

**Domanda:** ti basta verificare che lo studente riconosca la forma corretta oppure vuoi dimostrare che sappia costruire autonomamente una frase?

**Perché conta:** le sole domande a scelta multipla non verificano direttamente la produzione autonoma di frasi.

**Risposta consigliata:** per l'MVP limitarsi al riconoscimento della regola in esempi diversi. Definire un obiettivo concreto per ciascun argomento e controllare che le domande lo coprano. Rimandare la produzione autonoma ai futuri esercizi di completamento e correzione.

**La tua decisione:** vuoi che l'utente arrivi al livello che ha scelto.

**Chiarito in D17:** ampliare il percorso a tutti gli argomenti di grammatica A1 dell'inventario documentato, mantenendo A1 come unico livello. Completare il percorso grammaticale non attesta le altre competenze linguistiche del livello.

### D06 — E se una lezione durasse cinque minuti invece di quindici?

**Domanda:** i 15 minuti sono una durata da raggiungere oppure una stima indicativa di una sessione breve?

**Perché conta:** una spiegazione, tre esempi e sei domande potrebbero richiedere tempi diversi da quelli immaginati. La durata non è garantita dal numero di elementi.

**Risposta consigliata:** mantenere il formato fissato nella spec e trattare la durata come indicativa, senza timer. Misurare il tempo nelle prove; se la stima è sistematicamente sbagliata, correggere prima la descrizione della sessione, senza aggiungere esercizi solo per riempire minuti.

**La tua decisione:** associare un numero di minuti al livello degli esercizi e raggiungere sempre i 15 minuti.

**Chiarito in D19:** i 15 minuti sono un budget stimato basato sui contenuti; l'utente può impiegare meno o più tempo. Nessun timer obbligatorio o generazione automatica di altri esercizi per riempire minuti.

### D07 — Cosa significa superare il quiz, e cosa succede a chi continua a fallirlo?

**Domanda:** accetti una regola rigida di almeno cinque risposte corrette su sei, anche se lo studente resta sullo stesso argomento per diversi tentativi?

**Perché conta:** la soglia è una regola di avanzamento, non dimostra da sola la padronanza dell'argomento. Inoltre, ripetere contenuti dello stesso tipo potrebbe non risolvere una difficoltà di comprensione.

**Risposta consigliata:** mantenere la soglia attuale e nessun salto di argomento nell'MVP. Chiamare il risultato «argomento superato», senza attribuire un livello linguistico. Se durante la prova si fallisce tre volte di seguito, esaminare domande e spiegazioni prima di decidere se serva un cambiamento didattico; non introdurre subito un sistema adattivo.

**La tua decisione:** accetti il consiglio: almeno cinque risposte corrette su sei per avanzare, nessun salto di argomento e nessuna attestazione di livello. Nei test, fallimenti ripetuti porteranno a esaminare contenuti e spiegazioni prima di introdurre adattamento automatico.

### D08 — Chi si accorge di una risposta sbagliata generata dall'AI?

**Domanda:** chi può controllare che regola, soluzione, distrattori e motivazione siano corretti e comprensibili per A1?

**Perché conta:** una lezione può rispettare perfettamente lo schema e contenere un errore grammaticale o due risposte plausibili. Il punteggio deterministico confronta la scelta con la soluzione salvata: se quella soluzione è sbagliata, anche il risultato lo sarà.

**Risposta consigliata:** individuare una persona con competenza sufficiente a controllare un campione iniziale di almeno due lezioni per argomento. Verificare pertinenza, chiarezza, unicità della soluzione e coerenza della spiegazione. Gli errori trovati vanno corretti nel prompt o nei vincoli e il campione va ricontrollato. Un campione senza errori osservati non garantisce tutte le generazioni future; un secondo modello non sostituisce automaticamente questa verifica.

**La tua decisione:** in futuro vorresti un dataset con esercizi divisi per livello, eventualmente usato attraverso RAG per creare esercizi più precisi. Dataset e recupero dei contenuti restano fuori dall'MVP.

**Chiarito in D21:** la correttezza didattica della prima versione verrà controllata manualmente dall'autore. Il dataset resta futuro; il recupero da un dataset, da solo, non prova che le nuove varianti generate siano corrette.

## 3. Generazione AI e casi problematici

### D09 — Come esci da una lezione incompleta ma inutilizzabile?

**Domanda:** se una domanda è ambigua o incomprensibile, come riparti senza essere costretto a completare quella lezione?

**Perché conta:** la spec consente una sola lezione incompleta e impone di riprenderla. Al momento non definisce come abbandonarla: questo è un buco concreto nel flusso.

**Risposta consigliata:** valutare una piccola aggiunta esplicita, «Scarta lezione», disponibile solo prima dell'invio. Lo scarto non assegna un voto e non modifica i progressi; una nuova lezione viene generata solo quando si preme nuovamente «Inizia». È una modifica da approvare e riportare nella spec, non una funzionalità già inclusa. Per il primo test si può anche accettare un intervento manuale dello sviluppatore.

**La tua decisione:** sì a «Scarta lezione» per le lezioni non ancora inviate. Lo scarto non attribuisce un punteggio e non modifica i progressi; la rigenerazione richiede un nuovo avvio esplicito. Il costo già sostenuto per crearla dovrà restare registrato, in coerenza con D11.

### D10 — Quale provider puoi usare concretamente?

**Domanda:** hai già un account API utilizzabile e quale provider/modello vuoi impiegare nel primo test?

**Perché conta:** nel progetto non è ancora presente un'integrazione. Credenziali, disponibilità dell'accesso e comportamento delle risposte vanno verificati prima di collegare la generazione reale.

**Risposta consigliata:** partire da un provider già accessibile e da un solo modello che soddisfi il formato richiesto. Prima di integrare, verificarne la documentazione corrente e provare il campione di D08. Evitare confronti estesi fra provider e astrazioni per cambiarli finché non emerge un limite concreto.

**La tua decisione iniziale:** va bene un provider e un modello, con API key come richiesto in D11. D20 aggiorna la scelta tecnica: il client deve essere agnostico, con un solo provider/modello attivo alla volta.

**Chiarito in D20:** provider e modello saranno scelti in seguito, senza bloccare lo sviluppo del client comune. Non inserire chiavi API nei documenti.

### D11 — Quale spesa sei disposto a sostenere per la prova?

**Domanda:** qual è il budget massimo per il primo ciclo di sviluppo e utilizzo?

**Perché conta:** i nuovi tentativi e le ripetizioni degli argomenti generano altre richieste. Una richiesta di generazione più un eventuale nuovo tentativo non corrispondono a un costo già noto.

**Risposta consigliata:** scegliere un tetto esplicito, per esempio 10 € per il primo ciclo di prova. È una proposta di budget, non una stima dei prezzi del provider. Dopo la scelta di D10, verificare prezzi e consumo di alcune lezioni; usare gli strumenti del provider per controllare la spesa, distinguendo eventuali avvisi da veri limiti. Nessuna dashboard di fatturazione nell'app.

**La tua decisione:** utilizzare un provider con API key, senza limiti di spesa introdotti dall'app, con conteggio dei costi per ogni lezione creata. Il budget di esempio della raccomandazione iniziale non è adottato.

**Conseguenze per la specifica:** mostrare e salvare il costo di generazione della lezione. Per documentarlo con precisione, distinguere una stima calcolata da consumi e tariffe dalla fattura del provider; includere gli eventuali tentativi aggiuntivi attribuibili alla stessa generazione e conservare il costo anche se la lezione viene scartata. Un consumo non disponibile non deve diventare uno zero inventato. Consumi eventualmente sostenuti senza produrre una lezione vanno indicati separatamente quando noti. Tariffe e limiti effettivi si verificheranno sul provider scelto in D20; non si promette un servizio esterno illimitato.

### D12 — Quanto sei disposto ad aspettare una lezione?

**Domanda:** quale attesa massima rimane accettabile prima che «Inizia lezione» smetta di essere un'esperienza semplice?

**Perché conta:** la spec limita il numero di tentativi ma non il tempo totale. Un caricamento senza termine rende l'app apparentemente bloccata.

**Risposta consigliata:** proporre un limite complessivo di 60 secondi, includendo l'eventuale secondo tentativo; entro quel limite mostrare un caricamento chiaro, poi un errore recuperabile. Verificare la soglia con il provider scelto. Impedire richieste duplicate durante l'attesa; streaming e processi in background possono aspettare.

**La tua decisione:** accetti 60 secondi complessivi, compreso l'eventuale secondo tentativo, con caricamento chiaro, errore recuperabile e prevenzione delle richieste duplicate. Nessuno streaming o processo in background richiesto per l'MVP.

### D13 — È chiaro che “locale” non significa “senza Internet”?

**Domanda:** accetti che la generazione richieda una connessione e invii il contesto didattico a un servizio esterno?

**Perché conta:** applicazione e database possono risiedere sul computer, mentre il modello viene eseguito dal provider. Un requisito di funzionamento interamente offline cambierebbe la soluzione.

**Risposta consigliata:** usare un modello remoto per l'MVP, inviando solo argomento, obiettivi e istruzioni necessarie. Le risposte dello studente e lo storico non servono alla generazione prevista e restano locali. Senza connessione si può usare una lezione già salvata e correggerla; la creazione di nuove lezioni resta indisponibile con un messaggio chiaro.

**La tua decisione:** accetti il modello remoto e la necessità della connessione per creare nuove lezioni. Le lezioni già salvate e la loro correzione restano utilizzabili senza connessione. Si invia solo il contesto didattico; D18 rinvia la generazione mirata agli errori, quindi risposte e storico non vengono trasmessi al modello nell'MVP.

## 4. Confini pratici della prima versione

### D14 — Come immagini di aprire e usare l'app ogni giorno?

**Domanda:** per la prima versione ti va bene avviare il programma sul computer e aprirlo nel browser dello stesso computer?

**Perché conta:** uso da telefono, accesso da altri dispositivi e avvio come applicazione installata comportano lavoro diverso dal semplice funzionamento locale previsto.

**Risposta consigliata:** partire dal computer macOS attuale, con un browser desktop abituale e una breve procedura di avvio documentata. Rimandare distribuzione, accesso dalla rete e installazione automatica. Scegliere il browser su cui faremo la prima prova, senza creare subito una matrice di compatibilità.

**La tua decisione:** per adesso usare l'app sul tuo computer attuale, da browser. Restano fuori accesso da altri dispositivi, installazione come app e pubblicazione online.

### D15 — Quali dati ti aspetti di ritrovare, e in quali condizioni?

**Domanda:** accetti che le scelte non ancora inviate dipendano dal browser, mentre lezioni e risultati definitivi dipendono dal file del database locale?

**Perché conta:** cancellare i dati del browser può eliminare le selezioni provvisorie; perdere il database può eliminare lo storico. Ricaricare una pagina, cambiare browser e perdere un file sono situazioni differenti.

**Risposta consigliata:** mantenere questa distinzione per l'MVP e documentarla. Usare lo stesso browser durante una lezione; copiare manualmente il database ad app ferma prima di interventi sui dati. Evitare sincronizzazione e backup automatici nel primo rilascio. Per prove distruttive o ripartenze da zero usare un database di test separato.

**La tua decisione:** accetti selezioni provvisorie nel browser, lezioni e risultati nel database locale, stesso browser durante la sessione e copia manuale del database ad app ferma quando necessario. Nessuna sincronizzazione o procedura di backup automatica nell'MVP.

### D16 — Ti basta che il primo percorso abbia una fine?

**Domanda:** una volta superati i cinque argomenti, una schermata di completamento è sufficiente per lo scopo scelto in D01?

**Perché conta:** questo MVP permette di verificare un ciclo di studio finito, ma non offre un percorso duraturo né un ripasso libero dopo il completamento.

**Risposta consigliata:** mantenere la conclusione prevista dalla spec e usare quel momento per valutare D04. Se emerge una richiesta concreta di continuare o ripassare, scegliere una sola evoluzione e scrivere la sua spec. Non aggiungere adesso un intero curriculum per evitare che la prima prova finisca.

**La tua decisione:** mantenere la conclusione del percorso, ora esteso da D17 alla grammatica A1. In futuro si potrà ottimizzarlo con più lezioni per argomento e ripassi. Restano possibili i tentativi ripetuti necessari a superare un argomento.

## 5. Chiarimenti conclusivi

### D17 — Il raggiungimento del livello scelto è l'obiettivo futuro o un requisito del primo MVP?

**Domanda:** confermi che il primo MVP resta sui cinque argomenti introduttivi A1, oppure vuoi già una copertura completa di A1 o la scelta fra A1 e A2?

**Perché serve:** D05 descrive un obiettivo più ampio della spec attuale, mentre D16 mantiene la conclusione del percorso ridotto. Senza questa distinzione non possiamo definire curriculum e criteri di completamento coerenti.

**Risposta consigliata:** mantenere il primo MVP sui cinque argomenti A1 e documentarlo come percorso introduttivo. Raggiungere il livello scelto resta l'obiettivo del prodotto futuro. Se invece è un requisito immediato, occorre ampliare esplicitamente la spec; la sola grammatica a scelta multipla non va presentata come verifica di tutte le competenze del livello.

**La tua decisione:** includere tutti gli argomenti di grammatica A1, definiti attraverso una breve ricerca online. Il curriculum documentato in [A1-CURRICULUM.md](A1-CURRICULUM.md) sostituisce il percorso iniziale di cinque argomenti. A2 e la scelta fra livelli restano futuri; il completamento riguarda il curriculum grammaticale, non una certificazione A1.

### D18 — Che cosa deve ricordare il tutor, e come deve usare questa memoria già nell'MVP?

**Domanda:** con «e non le possibili lezioni successive e quelle svolte» intendi che non deve pensarci l'utente, oppure vuoi escludere la gestione delle lezioni e concentrarti soltanto sulle difficoltà?

**Perché serve:** salvare punteggi e storico non equivale a generare esercizi mirati sui punti deboli. La seconda possibilità cambia il valore centrale del prodotto e le informazioni necessarie al generatore.

**Risposta consigliata:** il tutor conserva lo storico e guida il prossimo passo, così l'utente non deve ricordarseli. Per l'MVP, definire «punto da migliorare» al livello dell'argomento: ricavarlo dai risultati salvati e proporre di nuovo quello non superato. Rinviare la memoria di errori specifici e le variazioni mirate a una versione successiva. Se invece vuoi già esercizi mirati, serve una decisione esplicita su quali difficoltà ricordare e sul loro uso, compreso il riepilogo trasmesso al modello.

**La tua decisione:** per adesso l'MVP salva lo storico. La memoria e l'eventuale salvataggio strutturato di errori specifici saranno aggiunti in futuro. Le risposte inviate restano nei risultati delle lezioni per poterli riaprire, ma non diventano un profilo degli errori o un contesto di personalizzazione.

### D19 — I 15 minuti devono essere stimati prima della sessione o misurati durante l'uso?

**Domanda:** vuoi una lezione con tempi assegnati che sommano sempre a 15 minuti, anche se l'utente impiega un tempo diverso, oppure vuoi che la sessione continui fino a 15 minuti reali?

**Perché serve:** nel primo caso basta una regola di composizione dei contenuti. Nel secondo servono decisioni su timer, pause, nuovi esercizi e fine della sessione: non è più il formato fisso della spec iniziale.

**Risposta consigliata:** budget stimato di 15 minuti, deciso dal backend con tempi associati al livello/difficoltà previsto, senza cronometro obbligatorio. Per il primo formato A1 si può partire da tre minuti per spiegazione ed esempi, nove per sei esercizi e tre per correzione, da calibrare nei test. La somma è sempre 15; il tempo reale non è garantito. Restando su sei esercizi si conserva anche la soglia approvata in D07.

**La tua decisione:** basare i 15 minuti sui contenuti creati, anche se l'utente impiega meno tempo. Rimane quindi un budget didattico stimato; il formato A1 iniziale usa tre minuti per spiegazione ed esempi, nove per sei esercizi e tre per correzione. Questi pesi sono una scelta iniziale da calibrare nei tuoi test, senza cambiare la durata reale dell'utente.

### D20 — Quale provider e modello configuriamo nel primo rilascio?

**Domanda:** quale provider con API key vuoi usare, e hai già scelto un modello oppure vuoi delegarne la scelta tecnica?

**Perché serve:** «va bene» approva l'approccio a provider singolo ma non identifica un'integrazione; il conteggio dei costi richiede anche una fonte tariffaria precisa per il modello configurato.

**Risposta consigliata:** usare il provider a cui hai già accesso; se non hai preferenze, delegare esplicitamente la scelta. In quel caso si confronteranno solo le informazioni necessarie nella documentazione ufficiale aggiornata e si sceglierà un unico modello. «Senza limiti» significa qui nessun tetto di spesa applicativo, conservando timeout e massimo di due tentativi concordati; disponibilità e limiti del servizio esterno andranno verificati.

**La tua decisione:** sceglierai il provider in seguito. Per adesso sviluppare le chiamate attraverso un client agnostico, per poter cambiare provider senza riscrivere il flusso didattico.

**Scelta tecnica per attuarla:** SDK Python LiteLLM usato direttamente, con modello, chiave e base URL eventuale configurabili sul backend e un solo modello attivo. Evitare gateway, router, fallback fra provider e una gerarchia di adattatori scritta nel progetto. La compatibilità dipende dai provider supportati dal client e dalle capacità del modello; non si promette supporto automatico per qualunque API. [Documentazione LiteLLM](https://docs.litellm.ai/docs/).

**Verifica rinviata, non dubbio di prodotto:** i test iniziali usano risposte simulate; le chiamate reali, la qualità didattica e le tariffe saranno verificate dopo la tua configurazione. L'MVP non va dichiarato collaudato sul provider prima di quella prova.

### D21 — Chi controlla le lezioni prima che esista il dataset futuro?

**Domanda:** per la prima versione, sarai tu a verificare anche correttezza di esercizi, soluzioni e spiegazioni durante i test?

**Perché serve:** hai già assunto la valutazione dell'utilità del prodotto; resta da distinguere il controllo didattico. Il dataset e il RAG sono futuri e non risolvono questa necessità nell'MVP.

**Risposta consigliata:** controllo manuale da parte tua su un piccolo campione per ogni argomento, verificando i casi dubbi con riferimenti affidabili. Documentare campione, problemi trovati e limiti della verifica, senza presentare la validazione dello schema come garanzia grammaticale. Non serve un secondo agente o un sistema di autovalutazione del prodotto.

**La tua decisione:** sì, sarai tu a controllare manualmente correttezza degli esercizi, soluzioni e spiegazioni durante i test, verificando i casi dubbi con riferimenti affidabili e documentando i limiti della verifica. Nessun sistema di autovalutazione del prodotto.

### D22 — Quanta pratica serve in una lezione da 15 minuti?

**Evidenza dai test d'uso:** sei esercizi sono troppo pochi anche nella sessione
breve da 15 minuti.

**La tua decisione:** ogni nuova lezione contiene tre blocchi da sei esercizi,
per un totale di 18. I blocchi allenano scelta della forma, completamento nel
contesto e correzione dell'errore. Restano tre opzioni e una sola soluzione per
mantenere la correzione deterministica; la soglia equivalente diventa 15/18.
Le vecchie lezioni da sei esercizi restano consultabili.

## Cosa possiamo decidere durante l'implementazione

Questi aspetti hanno già una direzione sufficiente e non richiedono altre domande di prodotto:

- Nomi di file, funzioni ed endpoint: scegliere la struttura più piccola che serve al flusso.
- Correzione e avanzamento: applicare le regole della spec e verificarne i casi limite.
- Ricaricamenti e invii ripetuti: recuperare la lezione salvata e restituire lo stesso risultato senza contare due volte il tentativo, anche quando la prima risposta del server è andata persa.
- Soluzioni, chiavi API e testi generati: mantenere i dati riservati sul backend e mostrare il testo senza eseguire HTML del modello.
- Dipendenze: usare gli strumenti già scelti senza introdurre livelli architetturali o componenti per funzionalità future.

## Quando abbiamo abbastanza chiarezza per procedere

Non serve prevedere ogni possibile evoluzione. Serve poter descrivere una sessione completa, compresi un errore e un nuovo tentativo, senza inventare decisioni di prodotto mentre la si sviluppa.

- [x] Scopo principale, responsabilità della valutazione personale e importanza della documentazione sono espliciti.
- [x] Copertura della grammatica A1, solo storico e 15 minuti stimati dai contenuti sono definiti: D17–D19.
- [x] Scarto delle lezioni, soglia di avanzamento 15/18 e fine del percorso
  attuale sono accettati.
- [x] Sono richiesti conteggio dei costi per lezione, nessun tetto di spesa applicativo e massimo 60 secondi di attesa.
- [x] Client agnostico, scelta successiva del provider e controllo didattico manuale sono definiti: D20–D21.
- [x] Uso locale da browser, persistenza dei dati e dipendenza dalla connessione per la generazione sono accettati.
- [x] Utilità e opportunità di proseguire saranno giudicate personalmente dall'autore sulla base dei propri test, senza un protocollo obbligatorio imposto dall'app.

Pianificazione allineata in [MVP-SPEC.md](docs/specs/MVP-SPEC.md), curriculum e fonti in [A1-CURRICULUM.md](A1-CURRICULUM.md), attività in [tasks.md](tasks.md). Il dataset per livello, l'eventuale RAG, più lezioni per argomento e i ripassi rimangono negli sviluppi successivi. La scelta del provider sarà una configurazione successiva, seguita dal collaudo reale previsto nelle attività.
