"""Session-backed quiz views and JSON APIs."""
from __future__ import annotations

import json

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .services import get_roster, make_question, normalize_name

SESSION_KEY = "brawl_quiz"


def _empty_state() -> dict:
    return {
        "correct": 0,
        "wrong": 0,
        "answered": 0,
        "total": 0,
        "deck": [],
        "current_en": None,
        "locked": False,
        "finished": False,
    }


def _get_state(request) -> dict:
    state = request.session.get(SESSION_KEY)
    if not isinstance(state, dict):
        state = _empty_state()
    return state


def _save_state(request, state: dict) -> None:
    request.session[SESSION_KEY] = state
    request.session.modified = True


def _stats(state: dict) -> dict:
    return {
        "correct": state.get("correct", 0),
        "wrong": state.get("wrong", 0),
        "answered": state.get("answered", 0),
        "total": state.get("total", 0),
    }


def _parse_json(request) -> dict:
    if not request.body:
        return {}
    try:
        data = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _error(message: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"ok": False, "message": message}, status=status)


@ensure_csrf_cookie
@require_GET
def index(request):
    return render(
        request,
        "quiz/index.html",
        {
            "round_seconds": getattr(settings, "QUIZ_ROUND_SECONDS", 24),
        },
    )


@require_POST
def api_start(request):
    """Start or restart a quiz session and return the first question."""
    try:
        roster = get_roster()
    except Exception:
        return _error("Could not load character data.", status=502)

    if len(roster) < 4:
        return _error("Not enough characters to build a quiz.")

    state = _empty_state()
    state["total"] = len(roster)
    state["deck"] = []

    try:
        current, deck, question = make_question(roster, state["deck"])
    except ValueError:
        return _error("Not enough characters to build a quiz.")

    state["deck"] = deck
    state["current_en"] = current["en"]
    state["locked"] = False
    state["finished"] = False
    _save_state(request, state)

    return JsonResponse(
        {
            "ok": True,
            "question": question,
            "stats": _stats(state),
            "finished": False,
            "round_seconds": getattr(settings, "QUIZ_ROUND_SECONDS", 24),
            "message": f"Quiz with {len(roster)} brawlers. Pick one of the four options.",
        }
    )


@require_POST
def api_answer(request):
    """Submit an answer or timeout for the current question."""
    state = _get_state(request)
    if not state.get("current_en"):
        return _error("Quiz has not started. Please start first.")
    if state.get("finished"):
        return _error("Quiz is finished. Please restart.")
    if state.get("locked"):
        return _error("This question has already been answered.")

    try:
        roster = get_roster()
    except Exception:
        return _error("Could not load character data.", status=502)

    payload = _parse_json(request)
    choice_en = payload.get("choice_en")
    timed_out = bool(payload.get("timeout"))

    current = next(
        (b for b in roster if normalize_name(b["en"]) == normalize_name(state["current_en"])),
        None,
    )
    if current is None:
        return _error("Current question data not found. Please restart.")

    if timed_out or choice_en is None:
        is_correct = None
    else:
        is_correct = normalize_name(choice_en) == normalize_name(current["en"])

    state["locked"] = True
    state["answered"] = int(state.get("answered", 0)) + 1

    if is_correct is True:
        state["correct"] = int(state.get("correct", 0)) + 1
        message = f"Correct! It was {current['name']}."
    elif is_correct is None:
        state["wrong"] = int(state.get("wrong", 0)) + 1
        message = f"Time's up! The answer was {current['name']}."
    else:
        state["wrong"] = int(state.get("wrong", 0)) + 1
        message = f"Close! The answer was {current['name']}."

    finished = state["answered"] >= state.get("total", 0)
    state["finished"] = finished
    if finished:
        message = "Quiz finished"

    _save_state(request, state)

    return JsonResponse(
        {
            "ok": True,
            "result": is_correct,
            "answer": {"name": current["name"], "en": current["en"]},
            "stats": _stats(state),
            "finished": finished,
            "message": message
            if not finished
            else f"Nice work! Correct {state['correct']} / Wrong {state['wrong']}",
            "finish_result": f"Correct {state['correct']} / Wrong {state['wrong']}"
            if finished
            else None,
        }
    )


@require_POST
def api_next(request):
    """Advance to the next question after the current one is locked."""
    state = _get_state(request)
    if state.get("finished"):
        return JsonResponse(
            {
                "ok": True,
                "finished": True,
                "stats": _stats(state),
                "message": "Quiz finished",
                "finish_result": f"Correct {state.get('correct', 0)} / Wrong {state.get('wrong', 0)}",
            }
        )
    if not state.get("locked"):
        return _error("Please answer first.")

    try:
        roster = get_roster()
    except Exception:
        return _error("Could not load character data.", status=502)

    try:
        current, deck, question = make_question(roster, state.get("deck") or [])
    except ValueError:
        return _error("Not enough characters to build a quiz.")

    state["deck"] = deck
    state["current_en"] = current["en"]
    state["locked"] = False
    _save_state(request, state)

    return JsonResponse(
        {
            "ok": True,
            "question": question,
            "stats": _stats(state),
            "finished": False,
            "round_seconds": getattr(settings, "QUIZ_ROUND_SECONDS", 24),
            "message": f"Quiz with {len(roster)} brawlers. Pick one of the four options.",
        }
    )


@require_GET
def api_status(request):
    state = _get_state(request)
    return JsonResponse(
        {
            "ok": True,
            "stats": _stats(state),
            "finished": bool(state.get("finished")),
            "has_question": bool(state.get("current_en")) and not state.get("finished"),
            "locked": bool(state.get("locked")),
            "round_seconds": getattr(settings, "QUIZ_ROUND_SECONDS", 24),
        }
    )
