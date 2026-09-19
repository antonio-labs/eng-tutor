const app = document.querySelector("#app");
const announcer = document.querySelector("#announcer");

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function button(label, className, action) {
  const node = element("button", `button ${className || ""}`.trim(), label);
  node.type = "button";
  node.addEventListener("click", action);
  return node;
}

function announce(message) {
  announcer.textContent = message;
}

function navigate(path) {
  window.location.hash = path;
}

function draftKey(lessonId) {
  return `lesson-draft:${lessonId}`;
}

function loadDraft(lessonId) {
  try {
    return JSON.parse(localStorage.getItem(draftKey(lessonId))) || {};
  } catch {
    return {};
  }
}

function saveDraft(lessonId, form, exercises) {
  const data = new FormData(form);
  const answers = {};
  for (const exercise of exercises) {
    const selected = data.get(exercise.id);
    if (selected !== null) answers[exercise.id] = Number(selected);
  }
  try {
    localStorage.setItem(draftKey(lessonId), JSON.stringify(answers));
  } catch {
    announce("Il browser non ha potuto salvare le selezioni provvisorie.");
  }
}

function clearDraft(lessonId) {
  try {
    localStorage.removeItem(draftKey(lessonId));
  } catch {
    // La risposta è già salvata sul backend; la bozza residua è innocua.
  }
}

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || "Richiesta non riuscita.");
  return body;
}

function showLoading() {
  const loading = element("div", "loading");
  loading.setAttribute("aria-label", "Caricamento in corso");
  for (let index = 0; index < 3; index += 1) {
    loading.append(element("div", "loading-block"));
  }
  app.replaceChildren(loading);
}

function showError(error) {
  const section = element("section");
  section.append(
    element("h1", "", "Non è stato possibile caricare la pagina"),
    element("p", "page-error", error.message),
    element("p", "", "Puoi riprovare senza perdere i dati già salvati."),
  );
  const actions = element("div", "actions");
  actions.append(
    button("Riprova", "", route),
    button("Torna alla home", "secondary", () => navigate("home")),
  );
  section.append(actions);
  app.replaceChildren(section);
  announce(error.message);
}

function costLabel(cost) {
  if (!cost || cost.status === "unavailable") return "Costo non disponibile";
  const amount = new Intl.NumberFormat("it-IT", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 4,
  }).format(cost.known_usd);
  return cost.status === "partial" ? `Subtotale parziale: ${amount}` : amount;
}

function dateLabel(value) {
  return new Intl.DateTimeFormat("it-IT", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

async function startLesson(event) {
  const startButton = event.currentTarget;
  startButton.disabled = true;
  startButton.textContent = "Preparazione...";
  announce("Preparazione della lezione in corso.");
  try {
    const lesson = await request("/api/lessons/start", { method: "POST" });
    navigate(`lesson/${lesson.id}`);
  } catch (error) {
    startButton.disabled = false;
    startButton.textContent = "Riprova";
    showError(error);
  }
}

function buildHistory(history) {
  const section = element("section", "section");
  const heading = element("div", "section-heading");
  heading.append(
    element("h2", "", "Lezioni precedenti"),
    element("p", "lede", "Risultati e lezioni scartate restano sul tuo computer."),
  );
  section.append(heading);
  if (history.length === 0) {
    section.append(element("p", "empty", "Lo storico è ancora vuoto."));
    return section;
  }

  const wrap = element("div", "history-wrap");
  const table = element("table", "history");
  const head = document.createElement("thead");
  const headRow = document.createElement("tr");
  for (const label of ["Argomento", "Data", "Esito", "Costo", "Azione"]) {
    headRow.append(element("th", "", label));
  }
  head.append(headRow);
  table.append(head);
  const body = document.createElement("tbody");
  for (const item of history) {
    const row = document.createElement("tr");
    row.append(
      element("td", "", item.unit.title),
      element("td", "", dateLabel(item.finished_at)),
      element(
        "td",
        "",
        item.status === "completed"
          ? `${item.correct_answers}/6, ${item.percentage}%`
          : "Scartata",
      ),
      element("td", "", costLabel(item.cost)),
    );
    const actionCell = document.createElement("td");
    if (item.status === "completed") {
      const open = element("button", "history-link", "Apri risultato");
      open.type = "button";
      open.addEventListener("click", () => navigate(`result/${item.id}`));
      actionCell.append(open);
    } else {
      actionCell.textContent = "Nessuna";
    }
    row.append(actionCell);
    body.append(row);
  }
  table.append(body);
  wrap.append(table);
  section.append(wrap);
  return section;
}

async function renderHome() {
  showLoading();
  const [summary, history] = await Promise.all([
    request("/api/summary"),
    request("/api/history"),
  ]);
  const hero = element("section", "hero");
  const copy = element("div");
  copy.append(element("p", "eyebrow", "Percorso di grammatica A1"));

  if (summary.path_completed) {
    copy.append(
      element("h1", "", "Percorso di grammatica A1 completato"),
      element("p", "lede", "Hai superato tutte le unità. I risultati restano consultabili nello storico."),
    );
  } else {
    copy.append(
      element("h1", "", summary.next_unit.title),
      element("p", "lede", summary.next_unit.objective),
    );
    const actions = element("div", "actions");
    actions.append(
      button(summary.active_lesson_id ? "Riprendi" : "Inizia", "", startLesson),
    );
    copy.append(actions);
  }

  const progress = element("aside", "progress-panel");
  progress.setAttribute("aria-label", "Progresso nel percorso");
  progress.append(
    element("p", "progress-number", `${summary.completed_units}/${summary.total_units}`),
    element("p", "progress-label", "unità superate"),
  );
  hero.append(copy, progress);
  app.replaceChildren(hero, buildHistory(history));
  app.focus();
}

function buildQuestion(exercise, index) {
  const fieldset = element("fieldset", "question");
  const legend = element("legend", "", `${index + 1}. ${exercise.question}`);
  fieldset.append(legend);
  exercise.options.forEach((option, optionIndex) => {
    const label = element("label", "option");
    const input = document.createElement("input");
    input.type = "radio";
    input.name = exercise.id;
    input.value = String(optionIndex);
    input.required = true;
    label.append(input, element("span", "", option));
    fieldset.append(label);
  });
  return fieldset;
}

async function renderLesson(id) {
  showLoading();
  const lesson = await request(`/api/lessons/${id}`);
  if (lesson.status === "completed") {
    navigate(`result/${id}`);
    return;
  }
  if (lesson.status === "discarded") {
    navigate("home");
    return;
  }

  const header = element("header", "lesson-header");
  const copy = element("div");
  copy.append(
    element("p", "eyebrow", lesson.unit.id),
    element("h1", "", lesson.unit.title),
    element("p", "lede", lesson.unit.objective),
  );
  const meta = element("aside", "meta-panel");
  meta.append(
    element("strong", "", "Lezione di esempio"),
    element("p", "", "Il contenuto attuale è simulato e non proviene da un provider AI."),
    element("p", "", `${lesson.content.timing.total_minutes} minuti stimati`),
  );
  header.append(copy, meta);

  const teaching = element("section", "lesson-copy");
  teaching.append(
    element("h2", "", "Regola"),
    element("p", "lede", lesson.content.explanation),
    element("h2", "", "Esempi"),
  );
  const examples = element("ul", "examples");
  for (const example of lesson.content.examples) {
    const item = element("li", "example");
    item.append(
      element("strong", "", example.sentence),
      element("span", "", example.note),
    );
    examples.append(item);
  }
  teaching.append(examples);

  const form = element("form", "quiz");
  form.append(element("h2", "", "Esercizi"));
  lesson.content.exercises.forEach((exercise, index) => {
    form.append(buildQuestion(exercise, index));
  });
  const draft = loadDraft(id);
  for (const exercise of lesson.content.exercises) {
    const selected = draft[exercise.id];
    if (Number.isInteger(selected) && selected >= 0 && selected < 3) {
      const input = form.querySelector(
        `input[name="${CSS.escape(exercise.id)}"][value="${selected}"]`,
      );
      if (input) input.checked = true;
    }
  }
  form.addEventListener("change", () => {
    saveDraft(id, form, lesson.content.exercises);
  });
  const message = element("p", "form-message");
  message.hidden = true;
  const actions = element("div", "actions");
  const submit = button("Invia risposte", "", () => form.requestSubmit());
  const discard = button("Scarta lezione", "danger", async () => {
    discard.disabled = true;
    try {
      await request(`/api/lessons/${id}/discard`, { method: "POST" });
      clearDraft(id);
      navigate("home");
    } catch (error) {
      message.textContent = error.message;
      message.hidden = false;
      discard.disabled = false;
    }
  });
  actions.append(submit, discard);
  form.append(message, actions);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    submit.disabled = true;
    submit.textContent = "Salvataggio...";
    const data = new FormData(form);
    const answers = Object.fromEntries(
      lesson.content.exercises.map((exercise) => [
        exercise.id,
        Number(data.get(exercise.id)),
      ]),
    );
    try {
      await request(`/api/lessons/${id}/submit`, {
        method: "POST",
        body: JSON.stringify({ answers }),
      });
      clearDraft(id);
      navigate(`result/${id}`);
    } catch (error) {
      message.textContent = error.message;
      message.hidden = false;
      submit.disabled = false;
      submit.textContent = "Invia risposte";
    }
  });

  app.replaceChildren(header, teaching, form);
  app.focus();
}

function answerReview(answer, index) {
  const article = element("article", "answer-review");
  article.dataset.correct = String(answer.is_correct);
  article.append(
    element("h3", "", `${index + 1}. ${answer.is_correct ? "Corretta" : "Da rivedere"}`),
  );
  const details = document.createElement("dl");
  details.append(
    element("dt", "", "Risposta"),
    element("dd", "", String(answer.selected_option + 1)),
    element("dt", "", "Soluzione"),
    element("dd", "", answer.solution),
    element("dt", "", "Perché"),
    element("dd", "", answer.rationale),
  );
  article.append(details);
  return article;
}

async function renderResult(id) {
  showLoading();
  const completed = await request(`/api/lessons/${id}/result`);
  const header = element("header", "result-header");
  const copy = element("div");
  copy.append(
    element("p", "eyebrow", completed.unit.id),
    element("h1", "", completed.result.passed ? "Argomento superato" : "Riprova l’argomento"),
    element(
      "p",
      "lede",
      completed.result.passed
        ? "Il prossimo avvio passerà all’unità successiva."
        : "Il prossimo avvio proporrà una nuova lezione sulla stessa unità.",
    ),
  );
  const score = element("aside", "meta-panel");
  score.append(
    element("p", "score", `${completed.result.correct_answers}/6`),
    element("p", "", `${completed.result.percentage}% corretto`),
    element("p", "", costLabel(completed.cost)),
  );
  header.append(copy, score);

  const review = element("section", "section");
  review.append(element("h2", "", "Correzione"));
  const grid = element("div", "answer-grid");
  completed.result.answers.forEach((answer, index) => {
    grid.append(answerReview(answer, index));
  });
  const actions = element("div", "actions section");
  actions.append(button("Torna alla home", "", () => navigate("home")));
  review.append(grid, actions);
  app.replaceChildren(header, review);
  app.focus();
}

async function route() {
  const [name = "home", id] = window.location.hash.replace(/^#\/?/, "").split("/");
  try {
    if (name === "lesson" && id) await renderLesson(id);
    else if (name === "result" && id) await renderResult(id);
    else await renderHome();
  } catch (error) {
    showError(error);
  }
}

window.addEventListener("hashchange", route);
route();
