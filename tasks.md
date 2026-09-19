# AI English Tutor — Attività di sviluppo MVP

Riferimento operativo: [MVP-SPEC.md](MVP-SPEC.md). Curriculum: [A1-CURRICULUM.md](A1-CURRICULUM.md). Motivazioni e decisioni: [MVP-GRILLING.md](MVP-GRILLING.md).

**Stato iniziale:** pianificazione completata, implementazione non iniziata. Ogni casella si chiude soltanto quando il comportamento è stato verificato. Il provider verrà scelto in seguito: questo non blocca lo sviluppo, ma la prova con un modello reale rimane necessaria prima di dichiarare l'MVP completo.

Procedere nell'ordine seguente, con modifiche piccole. Una sola applicazione, nessun componente predisposto per gli sviluppi futuri. Aggiornare le istruzioni di avvio mentre si implementa, così restano riproducibili.

## 1. Base del progetto e curriculum

- [x] **1.1 — Avvio locale.** Preparare il minimo progetto Python/FastAPI, dipendenze con versioni riproducibili e avvio sull'interfaccia locale. Aggiungere istruzioni iniziali e un esempio di configurazione senza segreti; escludere credenziali, database e file temporanei dal controllo versione.
- [x] **1.2 — Curriculum A1.** Tradurre le 36 unità della ricerca in un file JSON ordinato con ID stabili, titoli e obiettivi. Verificare corrispondenza con la tabella di copertura, unicità degli ID e obiettivi non vuoti; evitare copie divergenti del programma nel codice.
- [x] **1.3 — Modello della lezione.** Definire con Pydantic spiegazione, tre esempi e sei domande con tre opzioni, soluzione e motivazione. Separare la rappresentazione interna da quella inviata al browser. Assegnare il budget stimato 3 + 9 + 3 = 15 minuti nel backend.
- [x] **1.4 — Regole deterministiche.** Implementare correzione, punteggio e scelta della prima unità non superata. Verificare almeno: nessun risultato, 4/6, 5/6, tentativo ripetuto e tutte le unità superate. L'arrotondamento della percentuale non deve influenzare la soglia.

**Risultato verificabile:** una lezione di esempio viene validata e corretta senza chiamare modelli; il programma comprende tutte le unità previste e l'avanzamento funziona.

## 2. Persistenza e flusso applicativo

- [ ] **2.1 — Database locale.** Creare `lessons` e `generation_calls` con inizializzazione ripetibile, stati e campi previsti dalla spec. Conservare separatamente i consumi delle chiamate che non producono una lezione; ricavare i progressi dai risultati senza tabelle duplicate.
- [ ] **2.2 — Inizio e ripresa.** Esporre l'avvio/lettura di una lezione e il riepilogo del percorso, usando inizialmente un generatore simulato solo per sviluppo e test. Salvare prima di presentare; riutilizzare la lezione attiva. Impedire che avvii ravvicinati creino due lezioni attive o due generazioni concorrenti.
- [ ] **2.3 — Invio e risultato.** Validare ID, completezza e opzioni; correggere contro il contenuto salvato. Salvare risposte e completamento insieme, rendere il risultato immutabile e restituire lo stesso risultato a invii duplicati.
- [ ] **2.4 — Scarto e storico.** Aggiungere scarto prima dell'invio, elenco essenziale delle lezioni completate/scartate e riapertura dei risultati. Conservare i costi dello scarto, non avanzare e non rigenerare automaticamente. Rifiutare invii su lezioni scartate e scarti di lezioni completate.
- [ ] **2.5 — Verifica della persistenza.** Con un database temporaneo, verificare ripresa dopo riavvio, risultati stabili, scarto e nuovo avvio, errore di salvataggio recuperabile e invio ripetuto dopo perdita della risposta del server. Controllare che nessuna lettura precedente all'invio esponga soluzioni o motivazioni.

**Risultato verificabile:** il ciclo completo funziona sulle API con dati di esempio e sopravvive al riavvio; lo storico conserva tentativi e costi senza falsi avanzamenti.

## 3. Interfaccia utilizzabile

- [ ] **3.1 — Tre viste.** Realizzare home, lezione e risultato con HTML/CSS/JavaScript serviti dal backend. Usare il totale del curriculum per il progresso; rendere visibili storico, punteggi e costi senza dashboard o filtri aggiuntivi.
- [ ] **3.2 — Compilazione e recupero.** Salvare le selezioni provvisorie nel browser per lezione, ripristinarle al ricaricamento e cancellarle dopo invio riuscito/scarto. Gestire caricamento, doppio clic, errori recuperabili e fine del percorso; nessun timer obbligatorio.
- [ ] **3.3 — Prova del primo flusso.** Completare nel browser una lezione di esempio, riprenderla, scartarla e consultare un risultato precedente. Verificare navigazione da tastiera, etichette, testi leggibili e rendering sicuro dei contenuti. Usare un database di prova separato per simulare la fine del curriculum.

**Risultato verificabile:** si può usare l'app dall'inizio al risultato; in questa fase i contenuti di esempio sono dichiarati come tali e non dimostrano ancora l'integrazione AI.

## 4. Generazione reale, client agnostico e costi

- [ ] **4.1 — Client comune.** Collegare direttamente LiteLLM SDK in un piccolo modulo di generazione, con `LLM_MODEL`, `LLM_API_KEY` ed eventuale `LLM_API_BASE`. Un solo provider configurato alla volta; niente proxy, router, fallback fra provider o adattatori personalizzati. Se la configurazione manca, consentire l'accesso ai dati salvati e spiegare perché la generazione è indisponibile.
- [ ] **4.2 — Prompt e output.** Passare soltanto unità, obiettivo, A1, lingue e formato. Ottenere JSON e validarlo con il modello del blocco 1; usare output strutturati nativi quando supportati. Generare anche le motivazioni, così invio e feedback non chiamano il provider. Nei test sostituire solo la chiamata esterna.
- [ ] **4.3 — Errori e tempi.** Applicare un limite complessivo di 60 secondi e massimo due chiamate, disabilitando tentativi impliciti del client. Riprovare solo nei casi recuperabili con tempo residuo; gestire subito configurazione/credenziali errate. Registrare esiti incompleti o sconosciuti dopo interruzioni senza inventare consumi o lezioni.
- [ ] **4.4 — Conteggio dei costi.** Salvare per chiamata consumi disponibili, provider/modello, stima USD e riferimento tariffario. Aggregare i tentativi per lezione e mostrare totale, subtotale parziale o costo non disponibile. Conservare importi storici e costi delle lezioni scartate; evidenziare separatamente i consumi noti delle generazioni fallite. Nessun limite di spesa applicativo.
- [ ] **4.5 — Test dell'integrazione.** Simulare risposta valida, JSON non valido seguito da risposta valida, due fallimenti, timeout, credenziali errate, consumi assenti e prezzi mancanti. Verificare numero effettivo di chiamate, validazione, costi dei tentativi e assenza di richieste AI durante correzione/consultazione. Usare consumi e tariffe di prova deterministici, senza chiamate a pagamento.

**Risultato verificabile:** il flusso usa il client agnostico e gestisce contenuti, errori e costi. I test sono eseguibili senza API key; la compatibilità con un provider reale è ancora da collaudare.

## 5. Collaudo con il provider scelto e verifica didattica

- [ ] **5.1 — Configurazione successiva dell'autore.** Quando viene scelto il provider, configurare un modello supportato e verificare autenticazione, capacità di output, consumo restituito e tariffe nella documentazione ufficiale aggiornata. Registrare modello, data, versione del client e fonte dei prezzi, mai la chiave.
- [ ] **5.2 — Prova reale completa.** Generare e completare una lezione, controllare qualità dell'output, tempo totale e costo stimato. Verificare inoltre che una lezione già salvata sia consultabile e correggibile senza connessione e che un nuovo avvio non lo sia.
- [ ] **5.3 — Revisione dell'autore.** Controllare un piccolo campione per ciascuna delle 36 unità: pertinenza, vocabolario, soluzione unica e motivazioni corrette. Annotare gli errori, correggere prompt/vincoli e ricontrollare le parti coinvolte. La validazione automatica dello schema non sostituisce questa prova.
- [ ] **5.4 — Controllo finale della spec.** Percorrere i criteri di completamento di `MVP-SPEC.md`, riportando esito e limiti effettivi. Verificare che il client, la documentazione e l'interfaccia non dichiarino provider non testati o un raggiungimento certificato di A1.

**Risultato verificabile:** esiste evidenza della prova sul provider configurato e della revisione manuale dei contenuti. Se il provider non è ancora stato scelto, lasciare queste attività aperte senza bloccare i blocchi precedenti o la documentazione.

## 6. Documentazione per GitHub

- [ ] **6.1 — README riproducibile.** Descrivere problema, scope, flusso utente e architettura essenziale; includere prerequisiti, installazione, avvio, configurazione, test e soluzione dei problemi comuni. Provare le istruzioni in un ambiente pulito sul computer attuale.
- [ ] **6.2 — Trasparenza su contenuti e costi.** Collegare fonti e curriculum, spiegare i 15 minuti stimati, distinguere AI e logica deterministica, documentare uso dei dati, costo stimato rispetto alla fatturazione e modalità di backup manuale. Documentare lo stato del collaudo reale se il blocco 5 è ancora aperto.
- [ ] **6.3 — Demo fedele.** Aggiungere una breve sequenza di schermate o un esempio del flusso ottenuto dall'app funzionante, senza segreti o dati personali. Separare nel README funzionalità presenti, limiti osservati e roadmap: memoria degli errori, dataset/RAG, più lezioni per argomento e ripassi restano futuri.

**Risultato verificabile:** un visitatore del repository comprende cosa fa davvero l'MVP, lo può avviare seguendo le istruzioni e sa quali prove sono state eseguite. La pubblicazione su GitHub e il deployment non fanno parte di queste attività.
