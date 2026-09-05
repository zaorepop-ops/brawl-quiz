const MASKED_NAME = "？？？？？";

const roundSecondsEl = document.getElementById("quiz-round-seconds");
const ROUND_TIME = roundSecondsEl ? Number(JSON.parse(roundSecondsEl.textContent)) : 24;

const state = {
  locked: false,
  timer: null,
  timeLeft: ROUND_TIME,
  current: null,
  imageUrls: []
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

function getCookie(name) {
  const match = document.cookie.match(new RegExp("(?:^|; )" + name.replace(/([.$?*|{}()[\]\\/+^])/g, "\\$1") + "=([^;]*)"));
  return match ? decodeURIComponent(match[1]) : null;
}

async function api(path, options = {}) {
  const headers = Object.assign({ "Content-Type": "application/json" }, options.headers || {});
  const csrftoken = getCookie("csrftoken");
  if (csrftoken) headers["X-CSRFToken"] = csrftoken;

  const response = await fetch(path, {
    credentials: "same-origin",
    ...options,
    headers
  });

  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok || (data && data.ok === false)) {
    const message = (data && data.message) || "リクエストに失敗しました。";
    throw new Error(message);
  }
  return data;
}

function updateStats(stats) {
  if (!stats) return;
  els.correct.textContent = stats.correct ?? 0;
  els.wrong.textContent = stats.wrong ?? 0;
  els.answered.textContent = stats.answered ?? 0;
}

function showBrawlerImage(index = 0) {
  const urls = state.imageUrls || [];
  const url = urls[index];
  els.brawlerImage.dataset.imageIndex = String(index);
  els.avatar.classList.toggle("image-missing", !url);
  els.brawlerImage.src = url || "";
}

function clearTimer() {
  if (state.timer) {
    clearInterval(state.timer);
    state.timer = null;
  }
}

function startTimer(seconds) {
  clearTimer();
  state.timeLeft = seconds || ROUND_TIME;
  els.timerBar.style.transform = "scaleX(1)";
  state.timer = setInterval(() => {
    state.timeLeft -= 0.1;
    els.timerBar.style.transform = `scaleX(${Math.max(0, state.timeLeft / (seconds || ROUND_TIME))})`;
    if (state.timeLeft <= 0) {
      submitAnswer({ timeout: true });
    }
  }, 100);
}

function renderQuestion(payload) {
  const question = payload.question;
  state.locked = false;
  state.current = null;
  state.imageUrls = question.image_urls || [];

  els.stage.classList.remove("finished");
  els.avatar.style.background = `linear-gradient(145deg, ${question.color || "#4cc9f0"}, #10121a 76%)`;
  els.avatar.classList.remove("image-missing");
  els.brawlerImage.alt = "";
  els.avatarInitial.textContent = "?";
  els.maskedName.textContent = MASKED_NAME;
  els.timer.hidden = false;
  els.avatarWrap.hidden = false;
  els.maskedName.hidden = false;
  els.finishPanel.hidden = true;
  els.message.textContent = payload.message || "4択から選んでください。";
  els.next.hidden = false;
  els.next.disabled = true;
  els.answers.innerHTML = "";

  showBrawlerImage();
  (question.options || []).forEach(option => {
    const button = document.createElement("button");
    button.className = "answer";
    button.type = "button";
    button.textContent = option.name;
    button.dataset.en = option.en;
    button.addEventListener("click", () => submitAnswer({ choice_en: option.en, button }));
    els.answers.append(button);
  });

  updateStats(payload.stats);
  startTimer(payload.round_seconds || ROUND_TIME);
}

function showFinish(payload) {
  clearTimer();
  state.locked = true;
  els.stage.classList.add("finished");
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
  els.finishResult.textContent = payload.finish_result || payload.message || "";
  els.finishPanel.hidden = false;
  els.message.textContent = "クイズ終了";
  updateStats(payload.stats);
}

async function submitAnswer({ choice_en = null, timeout = false, button = null } = {}) {
  if (state.locked) return;
  state.locked = true;
  clearTimer();

  try {
    const data = await api("/api/answer/", {
      method: "POST",
      body: JSON.stringify({ choice_en, timeout })
    });

    const answerEn = data.answer?.en;
    els.answers.querySelectorAll(".answer").forEach(btn => {
      const isAnswer = btn.dataset.en === answerEn;
      btn.disabled = true;
      if (isAnswer) btn.classList.add("correct");
      if (data.result === false && button && btn === button) btn.classList.add("wrong");
    });

    if (data.answer) {
      els.avatarInitial.textContent = data.answer.en?.[0] || "?";
      els.maskedName.textContent = data.answer.name || "";
    }

    updateStats(data.stats);
    els.message.textContent = data.message || "";

    if (data.finished) {
      showFinish(data);
    } else {
      els.next.disabled = false;
    }
  } catch (err) {
    state.locked = false;
    els.message.textContent = err.message || "回答の送信に失敗しました。";
    els.next.disabled = false;
  }
}

async function startQuiz() {
  clearTimer();
  els.message.textContent = "読み込み中…";
  els.next.disabled = true;
  try {
    const data = await api("/api/start/", { method: "POST", body: "{}" });
    if (data.finished) {
      showFinish(data);
      return;
    }
    renderQuestion(data);
  } catch (err) {
    els.message.textContent = err.message || "キャラクター情報を読み込めませんでした。";
    els.next.disabled = true;
  }
}

async function nextQuestion() {
  if (!state.locked) return;
  els.next.disabled = true;
  try {
    const data = await api("/api/next/", { method: "POST", body: "{}" });
    if (data.finished) {
      showFinish(data);
      return;
    }
    renderQuestion(data);
  } catch (err) {
    els.message.textContent = err.message || "次の問題を取得できませんでした。";
    els.next.disabled = false;
  }
}

els.next.addEventListener("click", nextQuestion);
els.restart.addEventListener("click", startQuiz);
els.brawlerImage.addEventListener("error", () => {
  const nextIndex = Number(els.brawlerImage.dataset.imageIndex || "0") + 1;
  if (nextIndex < (state.imageUrls || []).length) {
    showBrawlerImage(nextIndex);
  } else {
    els.avatar.classList.add("image-missing");
  }
});

startQuiz();
