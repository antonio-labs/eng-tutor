# AI English Tutor

Prima base dell'MVP: API locale FastAPI, curriculum grammaticale A1 e logica
deterministica per validare e correggere una lezione. Generazione AI,
persistenza e interfaccia arriveranno nei task successivi.

## Avvio locale

Requisiti: [uv](https://docs.astral.sh/uv/) e Python 3.12.13 (uv puo installarlo
automaticamente).

```bash
uv sync --frozen
uv run --frozen uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

L'API e disponibile solo in locale su <http://127.0.0.1:8000>; la
documentazione interattiva e su <http://127.0.0.1:8000/docs>.

La configurazione futura del provider e mostrata in `.env.example`. Copiare il
file in `.env` solo quando servira e non inserire mai credenziali nei file
versionati.

## Test

```bash
uv run --frozen pytest
```

I test verificano il curriculum completo, lo schema della lezione di esempio,
la separazione fra dati interni e browser, correzione, soglia e avanzamento.
