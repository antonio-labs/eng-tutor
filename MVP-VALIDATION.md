# Collaudo dell'MVP

Data: 22 settembre 2026.

## Provider e formato

- Provider: DeepSeek.
- Modello configurato: `deepseek/deepseek-flash`, servito come
  `deepseek-flash` (DeepSeek-V4.1-Flash).
- Client: LiteLLM 1.101.0.
- Endpoint: quello predefinito del client; `LLM_API_BASE` non impostato.
- Credenziale: verificata tramite chiamata riuscita, mai registrata nei file o
  nell'output del collaudo.
- Formato: JSON Output nativo con `response_format={"type":"json_object"}` e
  validazione locale completa tramite Pydantic.

La prima richiesta con credito ha evidenziato che Chat Completions rifiuta lo
schema Pydantic inviato come `response_format`, nonostante LiteLLM lo segnalasse
come supportato. Il generatore usa ora il formato `json_object` documentato da
DeepSeek e mantiene lo schema nel prompt e nella validazione backend.

La [pagina ufficiale del modello e dei
prezzi](https://api-docs.deepseek.com/quick_start/pricing/) consultata il giorno
del collaudo riporta, per milione di token di `deepseek-flash`:

| Voce | Fuori punta | Punta |
| --- | ---: | ---: |
| Input con cache | $0,003 | $0,006 |
| Input senza cache | $0,15 | $0,30 |
| Output | $0,60 | $1,20 |

Le fasce di punta pubblicate sono 01:00–04:00 e 06:00–10:00 UTC dal lunedì al
venerdì. Le cifre salvate dall'app sono stime prodotte dalla mappa costi di
LiteLLM al momento della risposta, non la fattura DeepSeek.

## Prova reale end-to-end

Una lezione A1-01 è stata generata e salvata in un database temporaneo, poi il
servizio è stato riaperto senza generatore per simulare l'assenza di connessione.

| Misura | Esito |
| --- | ---: |
| Tempo di generazione | 12,170 s |
| Chiamate | 1 |
| Token prompt | 626 |
| Token completamento | 2.844 |
| Token totali | 3.470 |
| Costo stimato | $0,0018003 |
| Esempi / esercizi | 3 / 6 |
| Validazione Pydantic | riuscita |
| Riapertura offline | riuscita |
| Correzione offline | 6/6 |
| Risultato dopo riapertura | invariato |
| Nuova generazione offline | rifiutata come previsto |
| Chiamate prima/dopo le operazioni offline | 1 / 1 |

## Revisione delle 36 unità

È stata generata una lezione reale per ciascuna unità con quattro richieste
concorrenti. Tutte le 36 risposte sono arrivate al primo tentativo e hanno
superato lo schema. La revisione successiva ha controllato manualmente
pertinenza all'obiettivo, livello del vocabolario, unicità della soluzione e
coerenza della motivazione.

| Misura | Valore |
| --- | ---: |
| Chiamate iniziali | 36 |
| Tempo parete del batch | 92,278 s |
| Latenza per unità, min / mediana / max | 5,129 / 8,786 / 27,864 s |
| Token prompt / completamento / totali | 22.870 / 80.759 / 103.629 |
| Costo stimato del batch | $0,0518859 |

Esito per unità:

| Unità | Prima revisione | Esito finale |
| --- | --- | --- |
| A1-01 | Fuori perimetro: una domanda anticipava A1-02 | Accettata dopo rigenerazione |
| A1-02 | Accettata | Accettata |
| A1-03 | Ambigua: `An apple` e `The apple` erano entrambe possibili | Accettata dopo rigenerazione |
| A1-04–A1-07 | Accettate | Accettate |
| A1-08 | Ambigua: `got` era anche un passato grammaticalmente valido | Accettata dopo rigenerazione |
| A1-09–A1-13 | Accettate | Accettate |
| A1-14 | Distrattore grammaticalmente possibile: `Often she...` | Accettata dopo rigenerazione |
| A1-15 | Accettata | Accettata |
| A1-16 | Errata lingua target: insegnava i pronomi italiani | Accettata dopo rigenerazione |
| A1-17 | Errata lingua target: insegnava i possessivi italiani | Accettata dopo rigenerazione |
| A1-18–A1-36 | Accettate | Accettate |

Il prompt è stato corretto una sola volta per imporre grammatica target inglese,
perimetro stretto dell'unità, contesto autosufficiente e una sola opzione
inequivocabilmente corretta. Le sei unità respinte sono state rigenerate e
ricontrollate: 6/6 accettate. La seconda prova ha usato 19.841 token e ha avuto
un costo stimato di $0,01002585.

Il costo stimato delle 43 generazioni riuscite usate nel collaudo completo è
$0,06371205. I precedenti errori HTTP 402 e 400 non hanno restituito consumi o
stime e non sono inclusi nel totale.

## Criteri di completamento

| Criterio della specifica | Evidenza | Esito |
| --- | --- | --- |
| 36 unità ordinate con obiettivi | Curriculum JSON e test automatici | Superato |
| Flusso completo e conclusione | Test API/browser precedenti e prova reale sopra | Superato |
| Formato della lezione e 15 minuti | Modelli, test e 36 output reali | Superato |
| Punteggio, invii, scarto, soluzioni protette | Test automatici | Superato |
| Persistenza e gestione errori | Test automatici e riapertura offline reale | Superato |
| Client configurabile, 2 chiamate, 60 secondi | Configurazione, test retry/timeout e prova reale | Superato |
| Costi noti, parziali e mancanti | Test automatici e consumi reali sopra | Superato |
| Provider, formato, consumi, prezzi e tempi reali | DeepSeek `deepseek-flash`, 43 risposte riuscite | Superato |
| Campione manuale per ogni unità | 36 unità revisionate, 6 corrette e ricontrollate | Superato |
| README riproducibile e trasparente | README aggiornato e questo report | Superato |

Suite finale: 35 test superati con `uv run --frozen pytest -q`. I test
automatici non usano la chiave e non chiamano il provider.

## Limiti

- La revisione copre un campione per unità e non garantisce che ogni futura
  generazione sia didatticamente corretta.
- Il controllo è una revisione del contenuto generato, non una certificazione da
  parte di un docente o ente linguistico.
- È stato collaudato soltanto DeepSeek `deepseek-flash`; il client resta
  configurabile, ma non dichiara verificati altri provider.
- Il costo è una stima LiteLLM e può differire dalla fattura del provider.
- Il percorso copre la grammatica prevista dal curriculum, non certifica il
  raggiungimento complessivo del livello CEFR A1.
