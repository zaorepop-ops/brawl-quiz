const API_URL = "https://api.brawlapi.com/v1/brawlers";
const CONFIG = typeof BRAWL_QUIZ_CHARACTERS !== "undefined" ? BRAWL_QUIZ_CHARACTERS : {};
const ROUND_TIME = 24;
const MASKED_NAME = "？？？？？";
const IMAGE_SLUG_OVERRIDES = {
  "8-BIT": "8_bit",
  "EL-PRIMO": "el_primo",
  "JAE-YONG": "jae_yong",
  "LARRY-LAWRIE": "larry_and_lawrie",
  "MR-P": "mr_p",
  "R-T": "r_t"
};

let brawlers = [];

const state = {
  correct: 0,
  wrong: 0,
  answered: 0,
  current: null,
  questionDeck: [],
  locked: false,
  timer: null,
  timeLeft: ROUND_TIME
};

const els = {
  correct: document.querySelector("#correctCount"),
  wrong: document.querySelector("#wrongCount"),
  answered: document.querySelector("#answeredCount"),
  stage: document.querySelector(".brawler-stage"),
  timer: document.querySelector(".timer"),
  avatarWrap: document.querySelector(".avatar-wrap"),
  avatar: document.querySelector("#avatar"),
  brawlerImage: document.querySelector("#brawlerImage"),
  avatarInitial: document.querySelector("#avatarInitial"),
  maskedName: document.querySelector("#maskedName"),
  finishPanel: document.querySelector("#finishPanel"),
  finishResult: document.querySelector("#finishResult"),
  answers: document.querySelector("#answers"),
  message: document.querySelector("#message"),
  next: document.querySelector("#next"),
  restart: document.querySelector("#restart"),
  timerBar: document.querySelector("#timerBar")
};

function shuffle(items) {
  return [...items].sort(() => Math.random() - 0.5);
}

function normalizeName(name) {
  return String(name).trim().toUpperCase();
}

function titleCase(name) {
  return String(name).toLowerCase().replace(/\b[a-z]/g, char => char.toUpperCase());
}

function imageSlug(name) {
  const override = IMAGE_SLUG_OVERRIDES[normalizeName(name)];
  if (override) return override;

  return name
    .toLowerCase()
    .replace(/&/g, "and")
    .replace(/\./g, "")
    .replace(/\s+/g, "-");
}

function imageUrlsFor(apiBrawler, englishName) {
  return [
    `https://www.noff.gg/brawl-stars/res/img/brawlers/${imageSlug(englishName)}.webp`,
    apiBrawler.imageUrl,
    apiBrawler.imageUrl2
  ].filter(Boolean);
}

function fromApiBrawler(apiBrawler) {
  const en = titleCase(apiBrawler.name);
  const imageUrls = imageUrlsFor(apiBrawler, en);

  return {
    name: CONFIG.nameOverrides?.[normalizeName(apiBrawler.name)] || en,
    en,
    color: apiBrawler.rarity?.color || "#4cc9f0",
    imageUrls
  };
}

function buildRoster(apiBrawlers) {
  const excluded = new Set((CONFIG.excludedEnglishNames || []).map(normalizeName));
  const roster = apiBrawlers
    .filter(item => item.imageUrl)
    .map(fromApiBrawler)
    .filter(item => !excluded.has(normalizeName(item.en)));

  const existing = new Set(roster.map(item => normalizeName(item.en)));
  (CONFIG.extraBrawlers || []).forEach(item => {
    if (!existing.has(normalizeName(item.en)) && !excluded.has(normalizeName(item.en))) {
      roster.push(item);
    }
  });

  return roster;
}

function resetQuestionDeck() {
  state.questionDeck = shuffle(brawlers);
}

function pickQuestion() {
  if (state.questionDeck.length === 0) resetQuestionDeck();

  const current = state.questionDeck.pop();
  const choices = shuffle(brawlers.filter(item => item.en !== current.en)).slice(0, 3);

  return {
    current,
    options: shuffle([current, ...choices])
  };
}

function showBrawlerImage(index = 0) {
  const urls = state.current?.imageUrls || [];
  const url = urls[index];

  els.brawlerImage.dataset.imageIndex = String(index);
  els.avatar.classList.toggle("image-missing", !url);
  els.brawlerImage.src = url || "";
}

function updateStats() {
  els.correct.textContent = state.correct;
  els.wrong.textContent = state.wrong;
  els.answered.textContent = state.answered;
}

function startTimer() {
  clearInterval(state.timer);
  els.timerBar.style.transform = "scaleX(1)";

  state.timer = setInterval(() => {
    state.timeLeft -= 0.1;
    els.timerBar.style.transform = `scaleX(${Math.max(0, state.timeLeft / ROUND_TIME)})`;

    if (state.timeLeft <= 0) finishRound(null);
  }, 100);
}

function renderQuestion() {
  if (brawlers.length < 4) {
    els.message.textContent = "出題できるキャラクターが足りません。";
    els.next.disabled = true;
    return;
  }

  const question = pickQuestion();
  state.current = question.current;
  state.locked = false;
  state.timeLeft = ROUND_TIME;

  els.avatar.style.background = `linear-gradient(145deg, ${state.current.color}, #10121a 76%)`;
  els.avatar.classList.remove("image-missing");
  els.brawlerImage.alt = state.current.name;
  els.avatarInitial.textContent = "?";
  els.maskedName.textContent = MASKED_NAME;
  els.timer.hidden = false;
  els.avatarWrap.hidden = false;
  els.maskedName.hidden = false;
  els.finishPanel.hidden = true;
  els.message.textContent = `${brawlers.length}体から出題中。4択から選んでください。`;
  els.next.hidden = false;
  els.next.disabled = true;
  els.answers.innerHTML = "";

  showBrawlerImage();
  question.options.forEach(option => {
    const button = document.createElement("button");
    button.className = "answer";
    button.type = "button";
    button.textContent = option.name;
    button.dataset.en = option.en;
    button.addEventListener("click", () => answer(option, button));
    els.answers.append(button);
  });

  updateStats();
  startTimer();
}

function finishRound(isCorrect, clickedButton = null) {
  if (state.locked) return;

  state.locked = true;
  clearInterval(state.timer);

  els.answers.querySelectorAll(".answer").forEach(button => {
    const isAnswer = button.dataset.en === state.current.en;
    button.disabled = true;
    if (isAnswer) button.classList.add("correct");
    if (isCorrect === false && button === clickedButton) button.classList.add("wrong");
  });

  els.avatarInitial.textContent = state.current.en[0];
  els.maskedName.textContent = state.current.name;
  state.answered += 1;

  if (isCorrect) {
    state.correct += 1;
    els.message.textContent = `正解！ ${state.current.name} でした。`;
  } else if (isCorrect === null) {
    state.wrong += 1;
    els.message.textContent = `時間切れ！ 正解は ${state.current.name} でした。`;
  } else {
    state.wrong += 1;
    els.message.textContent = `おしい！ 正解は ${state.current.name} でした。`;
  }

  updateStats();

  if (state.answered >= brawlers.length) {
    finishQuiz();
  } else {
    els.next.disabled = false;
  }
}

function answer(option, clickedButton) {
  if (!state.locked) finishRound(option.en === state.current.en, clickedButton);
}

function restart() {
  state.correct = 0;
  state.wrong = 0;
  state.answered = 0;
  resetQuestionDeck();
  renderQuestion();
}

function finishQuiz() {
  clearInterval(state.timer);
  els.next.hidden = true;
  els.next.disabled = true;
  els.answers.innerHTML = "";
  els.timer.hidden = true;
  els.avatarWrap.hidden = true;
  els.avatar.classList.add("image-missing");
  els.brawlerImage.src = "";
  els.avatarInitial.textContent = "";
  els.maskedName.hidden = true;
  els.maskedName.textContent = "";
  els.finishResult.textContent = `正解 ${state.correct} / 不正解 ${state.wrong}`;
  els.finishPanel.hidden = false;
  els.message.textContent = "クイズ終了";
}

async function loadRoster() {
  try {
    const response = await fetch(API_URL);
    if (!response.ok) throw new Error("Could not load brawler data.");

    const data = await response.json();
    brawlers = buildRoster(data.list);
    resetQuestionDeck();
    renderQuestion();
  } catch {
    els.message.textContent = "キャラクター情報を読み込めませんでした。";
    els.next.disabled = true;
  }
}

els.next.addEventListener("click", renderQuestion);
els.restart.addEventListener("click", restart);
els.brawlerImage.addEventListener("error", () => {
  const nextIndex = Number(els.brawlerImage.dataset.imageIndex || "0") + 1;
  const urls = state.current?.imageUrls || [];

  if (nextIndex < urls.length) {
    showBrawlerImage(nextIndex);
  } else {
    els.avatar.classList.add("image-missing");
  }
});

loadRoster();
