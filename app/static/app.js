const app = document.querySelector("#app");
const announcer = document.querySelector("#announcer");
const practiceBlocks = [
  {
    type: "form_choice",
    title: "1. Scegli la forma corretta",
    description: "Riconosci la forma grammaticale richiesta dalla frase.",
  },
  {
    type: "context_completion",
    title: "2. Completa nel contesto",
    description: "Usa le informazioni del breve contesto per completare la frase.",
  },
  {
    type: "error_correction",
    title: "3. Trova la frase corretta",
    description: "Confronta le alternative e individua l’unica frase corretta.",
  },
];

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function textNode(text) {
  const node = document.createTextNode("");
  node.textContent = text;
  return node;
}

function appendInlineMarkdown(parent, source) {
  const pattern = /(\*\*[^*\n]+\*\*|`[^`\n]+`)/g;
  let offset = 0;
  for (const match of source.matchAll(pattern)) {
    if (match.index > offset) {
      parent.append(textNode(source.slice(offset, match.index)));
    }
    const marker = match[0][0];
    const tag = marker === "`" ? "code" : "strong";
    const markerLength = marker === "`" ? 1 : 2;
    parent.append(
      element(tag, "", match[0].slice(markerLength, -markerLength)),
    );
    offset = match.index + match[0].length;
  }
  if (offset < source.length) {
    parent.append(textNode(source.slice(offset)));
  }
}

function renderExplanationMarkdown(source) {
  const container = element("div", "explanation");
  let paragraph = [];
  let list = null;
  let quote = [];

  function appendTextBlock(parent, tag, lines) {
    if (lines.length === 0) return;
    const node = element(tag);
    appendInlineMarkdown(node, lines.join(" "));
    parent.append(node);
    lines.length = 0;
  }

  function flush() {
    appendTextBlock(container, "p", paragraph);
    if (list) {
      container.append(list);
      list = null;
    }
    if (quote.length > 0) {
      const blockquote = element("blockquote");
      appendTextBlock(blockquote, "p", quote);
      container.append(blockquote);
    }
  }

  for (const rawLine of source.replaceAll("\r\n", "\n").split("\n")) {
    const line = rawLine.trim();
    if (!line) {
      flush();
      continue;
    }

    const heading = line.match(/^###\s+(.+)$/);
    const item = line.match(/^[-*+]\s+(.+)$/);
    const quoted = line.match(/^>\s?(.*)$/);
    if (heading) {
      flush();
      const node = element("h3");
      appendInlineMarkdown(node, heading[1]);
      container.append(node);
    } else if (item) {
      if (paragraph.length > 0 || quote.length > 0) flush();
      if (!list) list = element("ul");
      const node = element("li");
      appendInlineMarkdown(node, item[1]);
      list.append(node);
    } else if (quoted) {
      if (paragraph.length > 0 || list) flush();
      quote.push(quoted[1]);
    } else {
      if (list || quote.length > 0) flush();
      paragraph.push(line);
    }
  }
  flush();
  return container;
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
          ? `${item.correct_answers}/${item.total_exercises}, ${item.percentage}%`
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

function buildFailedGenerations(generations) {
  if (generations.length === 0) return null;

  const section = element("section", "section failed-generations");
  const heading = element("div", "section-heading");
  heading.append(
    element("h2", "", "Generazioni senza lezione"),
    element(
      "p",
      "lede",
      "Tentativi conclusi senza creare una lezione. I costi noti restano separati dallo storico.",
    ),
  );
  const list = element("ul", "generation-list");
  for (const generation of generations) {
    const item = element("li", "generation-item");
    item.append(
      element("p", "generation-model", generation.model),
      element(
        "p",
        "generation-meta",
        `${dateLabel(generation.created_at)} · ${generation.calls} ${generation.calls === 1 ? "chiamata" : "chiamate"}`,
      ),
      element("p", "generation-meta", `Esiti: ${generation.outcomes.join(", ")}`),
      element("p", "generation-cost", costLabel(generation.cost)),
    );
    list.append(item);
  }
  section.append(heading, list);
  return section;
}

async function renderHome() {
  showLoading();
  const [summary, history, failedGenerations] = await Promise.all([
    request("/api/summary"),
    request("/api/history"),
    request("/api/generations/failed"),
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
    if (summary.active_lesson_id || summary.generation_available) {
      const actions = element("div", "actions");
      actions.append(
        button(summary.active_lesson_id ? "Riprendi" : "Inizia", "", startLesson),
      );
      copy.append(actions);
    } else {
      copy.append(
        element("p", "form-message", summary.generation_unavailable_reason),
      );
    }
  }

  const progress = element("aside", "progress-panel");
  progress.setAttribute("aria-label", "Progresso nel percorso");
  progress.append(
    element("p", "progress-number", `${summary.completed_units}/${summary.total_units}`),
    element("p", "progress-label", "unità superate"),
  );
  hero.append(copy, progress);
  const sections = [hero, buildHistory(history)];
  const failed = buildFailedGenerations(failedGenerations);
  if (failed) sections.push(failed);
  app.replaceChildren(...sections);
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
    element("strong", "", "Sessione breve"),
    element(
      "p",
      "",
      lesson.content.exercises.length === 18
        ? "Spiegazione, tre esempi e tre blocchi da sei esercizi."
        : `Spiegazione, tre esempi e ${lesson.content.exercises.length} esercizi.`,
    ),
    element("p", "", `${lesson.content.timing.total_minutes} minuti stimati`),
  );
  header.append(copy, meta);

  const teaching = element("section", "lesson-copy");
  teaching.append(
    element("h2", "", "Regola"),
    renderExplanationMarkdown(lesson.content.explanation),
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
  form.append(element("h2", "", "Pratica"));
  let questionNumber = 0;
  for (const block of practiceBlocks) {
    const exercises = lesson.content.exercises.filter(
      (exercise) => exercise.practice_type === block.type,
    );
    if (exercises.length === 0) continue;
    const section = element("section", "practice-block");
    section.append(
      element("h3", "", block.title),
      element("p", "practice-description", block.description),
    );
    for (const exercise of exercises) {
      section.append(buildQuestion(exercise, questionNumber));
      questionNumber += 1;
    }
    form.append(section);
  }
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
    element("dd", "", answer.selected_answer),
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
    element(
      "p",
      "score",
      `${completed.result.correct_answers}/${completed.result.total_exercises}`,
    ),
    element("p", "", `${completed.result.percentage}% corretto`),
    element("p", "", costLabel(completed.cost)),
  );
  header.append(copy, score);

  const review = element("section", "section");
  review.append(element("h2", "", "Correzione"));
  let answerNumber = 0;
  for (const block of practiceBlocks) {
    const answers = completed.result.answers.filter(
      (answer) => answer.practice_type === block.type,
    );
    if (answers.length === 0) continue;
    const blockReview = element("section", "practice-review");
    blockReview.append(element("h3", "", block.title));
    const grid = element("div", "answer-grid");
    for (const answer of answers) {
      grid.append(answerReview(answer, answerNumber));
      answerNumber += 1;
    }
    blockReview.append(grid);
    review.append(blockReview);
  }
  const actions = element("div", "actions section");
  actions.append(button("Torna alla home", "", () => navigate("home")));
  review.append(actions);
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
