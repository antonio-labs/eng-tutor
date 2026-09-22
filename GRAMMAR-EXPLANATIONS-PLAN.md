# Piano di implementazione — spiegazioni grammaticali A1

**Stato:** completato e verificato il 22 settembre 2026. Le evidenze automatiche,
editoriali e browser sono registrate in [MVP-VALIDATION.md](MVP-VALIDATION.md).

Questo piano estende l'MVP descritto in [MVP-SPEC.md](docs/specs/MVP-SPEC.md) senza
riaprire le attività già completate in [tasks.md](tasks.md). Le fonti e il
perimetro delle 36 unità restano quelli di [A1-CURRICULUM.md](A1-CURRICULUM.md);
la ricerca editoriale di supporto è raccolta in
[research/grammar-explanation-sources.md](research/grammar-explanation-sources.md).

## Obiettivo

Fornire a tutte le 36 unità A1 una spiegazione originale, approfondita entro lo
scope della singola unità, versionata nel backend e visualizzata in Markdown.
L'LLM deve usare la spiegazione verificata come contesto e generare soltanto i
tre esempi e i sei esercizi con relative motivazioni.

Il risultato deve conservare il flusso attuale della lezione, i dati già
salvati e il budget didattico di 15 minuti.

## Decisioni già prese

1. Le spiegazioni sono contenuto editoriale del backend, non output generato a
   ogni lezione.
2. Ogni unità ha un file `app/data/grammar_explanations/A1-NN.md`.
3. `LessonContent.explanation` resta una stringa, ma il suo contratto diventa
   Markdown. Il testo semplice già salvato rimane quindi valido e non serve una
   migrazione del database.
4. La lezione salva una copia della spiegazione insieme a esempi ed esercizi:
   modificare un file in futuro non riscrive lo storico.
5. L'interfaccia del generatore riceve un Contenuto dell’unità già verificato;
   la separazione tra contenuto curato e pratica generata rimane nascosta nella
   sua implementazione.
6. Il browser interpreta come Markdown soltanto `explanation`. Titoli, esempi,
   domande, opzioni e motivazioni continuano a essere mostrati come testo.
7. Per l'MVP si usa un sottoinsieme sicuro di Markdown senza HTML, immagini o
   link. Non si aggiungono CMS, RAG, database vettoriali o ingestione dei PDF.
8. Le fonti servono per verifica e impostazione didattica. Testi, esempi ed
   esercizi devono essere originali; estratti e libri non diventano un dataset.

## Flusso finale

```text
file Markdown verificato
        |
        v
caricamento per unit_id -----> contesto del prompt
        |                            |
        |                            v
        |                    esempi + esercizi AI
        |                            |
        +----------> LessonContent <-+
                          |
                     snapshot SQLite
                          |
                  renderer Markdown sicuro
```

## Contratto editoriale

Ogni file non contiene un titolo principale, perché ID, titolo e obiettivo sono
già mostrati dalla pagina. Usa invece questa struttura:

```md
### Quando si usa

Spiegazione semplice del significato e del contesto comunicativo.

### Come si forma

- Regola o formula essenziale.
- Eventuali forme affermative, negative o interrogative comprese nell'obiettivo.

### Attenzione

> Un limite, un contrasto o un'interferenza frequente per un italofono.

### Errori comuni

- Forma errata e relativa correzione, con motivo breve.
```

Regole editoriali:

- coprire completamente l'obiettivo dell'unità, senza anticipare argomenti A2 o
  unità successive;
- usare italiano chiaro e vocabolario inglese A1;
- privilegiare regole operative, contrasti e formule rispetto a definizioni
  astratte;
- includere solo i micro-esempi necessari a capire la regola, senza duplicare
  la sezione dei tre esempi della lezione;
- includere almeno un errore plausibile per un italofono;
- mantenere una lettura indicativa di 2-3 minuti, normalmente 160-240 parole;
- verificare i fatti sulle fonti mappate nel curriculum, senza copiarne la
  formulazione o gli esercizi.

Il conteggio delle parole è una guida editoriale, non una validazione rigida.
Alcuni argomenti richiedono naturalmente meno testo di altri.

## Ordine di implementazione

### Task 1 — Definire caricamento e validazione dei file Markdown

**Dipendenze:** nessuna.

**Modifiche:**

- creare `app/data/grammar_explanations/`;
- concentrare in `app/course.py` caricamento e validazione dell’intero percorso;
- caricare esclusivamente file corrispondenti agli ID del curriculum, in UTF-8;
- rifiutare file mancanti o vuoti con un errore che indichi chiaramente l'ID;
- non duplicare titoli, obiettivi o fonti nei file Markdown.

**Criteri di completamento:**

- un ID noto restituisce il contenuto del relativo file senza modificarlo;
- un ID sconosciuto o un file mancante produce un errore esplicito;
- il chiamante non deve conoscere directory o convenzioni dei nomi file;
- esiste un test piccolo del caricamento e dei casi di errore.

### Task 2 — Introdurre il renderer Markdown sicuro

**Dipendenze:** nessuna; può procedere in parallelo al Task 1.

**Modifiche:**

- sostituire il paragrafo singolo della spiegazione in `app/static/app.js` con
  un contenitore costruito dal renderer;
- supportare soltanto paragrafi, titoli `###`, elenchi puntati, citazioni,
  `**grassetto**` e `` `codice inline` ``;
- costruire nodi DOM e assegnare contenuti tramite `textContent`, senza
  `innerHTML`;
- trattare HTML e sintassi non supportata come testo inerte;
- aggiungere in `app/static/style.css` spaziatura, gerarchia tipografica e
  stile del richiamo `Attenzione`, mantenendo leggibilità da mobile;
- aggiornare la spiegazione di esempio affinché eserciti il formato Markdown.

**Criteri di completamento:**

- una spiegazione Markdown mostra sezioni, lista, enfasi e richiamo;
- una vecchia spiegazione in testo semplice continua a essere leggibile;
- stringhe contenenti HTML non producono elementi eseguibili;
- navigazione da tastiera e gerarchia dei titoli rimangono corrette;
- il test che vieta `innerHTML` continua a passare.

### Task 3 — Scrivere le tre spiegazioni pilota

**Dipendenze:** Task 1.

Creare e revisionare:

- `A1-01.md`: forme del presente di *be* e interferenze dell'italiano;
- `A1-03.md`: nomi, plurali e scelta degli articoli come regole decisionali;
- `A1-27.md`: contrasto fra presente semplice e progressivo.

Le tre unità sono scelte perché verificano rispettivamente paradigma, decisione
e contrasto fra strutture.

**Criteri di completamento:**

- ogni file segue il contratto editoriale;
- ogni affermazione rientra nell'obiettivo dell'unità;
- il testo è originale e controllato sulle fonti del curriculum;
- le tre spiegazioni vengono provate nell'interfaccia reale;
- tono, lunghezza e densità vengono approvati prima di produrre le altre 33.

### Task 4 — Popolare le restanti unità A1

**Dipendenze:** approvazione del Task 3.

Procedere in quattro lotti revisionabili:

- **4A — Fondamenta:** A1-02 e A1-04–A1-11;
- **4B — Presente e funzioni:** A1-12–A1-21;
- **4C — Quantità e forme verbali:** A1-22–A1-26;
- **4D — Passato, futuro e confronti:** A1-28–A1-36.

Per ogni lotto:

1. preparare una prima stesura originale usando obiettivo e fonti mappate;
2. controllare accuratezza, scope, progressione e interferenze dell'italiano;
3. leggere il contenuto nel renderer, non soltanto nel file sorgente;
4. correggere prima di iniziare il lotto successivo.

**Criteri di completamento:**

- esistono esattamente 36 file, uno per ciascun ID del curriculum;
- non esistono file orfani o ID duplicati;
- tutte le spiegazioni rispettano il contratto editoriale;
- nessuna spiegazione contiene testo provvisorio o copiato dalle fonti.

### Task 5 — Rendere verificabile la copertura editoriale

**Dipendenze:** Task 4.

**Modifiche:**

- estendere `tests/test_core.py` per confrontare gli ID del curriculum con i
  nomi dei file Markdown;
- verificare presenza delle quattro sezioni obbligatorie e contenuto non vuoto;
- rifiutare le funzionalità Markdown escluse dal contratto, senza tentare di
  dimostrare automaticamente la correttezza grammaticale;
- aggiungere una checklist di revisione con esito per tutte le 36 unità in
  `MVP-VALIDATION.md` o in un documento di validazione dedicato.

**Criteri di completamento:**

- una spiegazione assente, orfana o strutturalmente incompleta fa fallire i
  test;
- la correttezza didattica è attestata dalla revisione editoriale, non da
  euristiche fragili nel codice.

### Task 6 — Limitare l'LLM a esempi ed esercizi

**Dipendenze:** Task 5.

**Modifiche:**

- introdurre in `app/generation.py` un modello interno per il solo output AI:
  tre esempi e sei esercizi;
- rimuovere `unit_id` e `explanation` dallo schema richiesto al provider;
- inserire nel prompt obiettivo e spiegazione Markdown verificata come contesto
  da rispettare, non da riscrivere;
- assemblare internamente il `LessonContent` finale usando ID e spiegazione del
  backend più la pratica restituita dall'LLM;
- mantenere il provider dietro una sola interfaccia di generazione;
- aggiornare il generatore di esempio e i relativi fixture/test.

**Criteri di completamento:**

- il provider non può sostituire la spiegazione né l'ID dell'unità;
- ogni prompt contiene la spiegazione corretta per l'unità richiesta;
- il `LessonContent` salvato contiene una copia del Markdown verificato;
- retry, timeout, costi e validazione delle domande continuano a funzionare;
- correggere, riaprire o visualizzare una lezione non effettua chiamate AI.

### Task 7 — Verificare compatibilità e flusso completo

**Dipendenze:** Task 2 e Task 6.

**Verifiche automatiche:**

- eseguire l'intera suite `pytest`;
- controllare che una lezione storica con spiegazione in testo semplice venga
  ancora deserializzata e mostrata;
- controllare che soluzioni e motivazioni non arrivino al browser prima
  dell'invio;
- verificare che contenuti Markdown ostili restino testo inerte;
- verificare generazione valida, retry su JSON non valido e costi come prima.

**Verifiche manuali:**

- completare una lezione pilota da desktop e da viewport mobile;
- controllare ritmo di lettura, gerarchia visiva, callout ed esempi;
- riaprire una lezione salvata dopo avere modificato il file Markdown sorgente
  e confermare che lo snapshot storico non cambi.

**Criteri di completamento:** tutti i test passano e il flusso completo è
utilizzabile senza regressioni osservate.

### Task 8 — Allineare documentazione e specifica

**Dipendenze:** Task 7.

**Modifiche:**

- aggiornare `docs/specs/MVP-SPEC.md`: spiegazione Markdown curata nel backend e output AI
  limitato alla pratica;
- aggiornare `README.md`: posizione dei file, formato supportato e procedura per
  modificare una spiegazione;
- registrare in `MVP-VALIDATION.md` provider, prova reale e revisione delle 36
  spiegazioni;
- segnare questo piano come completato soltanto dopo il collaudo.

**Criteri di completamento:** documentazione, comportamento e test descrivono lo
stesso sistema, senza dichiarare RAG, uso dei PDF come dataset o funzionalità
Markdown non implementate.

## Definizione complessiva di completamento

Il lavoro è concluso quando:

- tutte le 36 unità hanno una spiegazione Markdown revisionata e versionata;
- il browser la rende in modo leggibile e sicuro;
- l'LLM genera solo esempi ed esercizi coerenti con la spiegazione;
- il database conserva lo snapshot di ogni lezione senza migrazioni distruttive;
- test automatici, revisione editoriale e prova manuale sono documentati;
- non sono state aggiunte infrastrutture previste soltanto per sviluppi futuri.
