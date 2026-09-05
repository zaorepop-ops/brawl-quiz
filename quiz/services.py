"""BrawlAPI roster loading, caching, and quiz question helpers."""
from __future__ import annotations

import random
import re
import threading
import time
from typing import Any

import requests
from django.conf import settings

from .characters_config import (
    EXCLUDED_ENGLISH_NAMES,
    EXTRA_BRAWLERS,
    IMAGE_SLUG_OVERRIDES,
    NAME_OVERRIDES,
)

_cache_lock = threading.Lock()
_roster_cache: dict[str, Any] = {"brawlers": None, "fetched_at": 0.0}


def normalize_name(name: str) -> str:
    return str(name).strip().upper()


def name_override_keys(name: str) -> list[str]:
    """Match overrides whether API uses spaces or hyphens."""
    n = normalize_name(name)
    variants = {n, n.replace(" ", "-"), n.replace("-", " ")}
    return list(variants)


def resolve_display_name(api_name: str, fallback: str) -> str:
    for key in name_override_keys(api_name):
        if key in NAME_OVERRIDES:
            return NAME_OVERRIDES[key]
    return fallback


def title_case(name: str) -> str:
    return re.sub(r"\b[a-z]", lambda m: m.group(0).upper(), str(name).lower())


def image_slug(name: str) -> str:
    override = IMAGE_SLUG_OVERRIDES.get(normalize_name(name))
    if override:
        return override
    slug = name.lower().replace("&", "and").replace(".", "")
    slug = re.sub(r"\s+", "-", slug)
    return slug


def image_urls_for(api_brawler: dict, english_name: str) -> list[str]:
    urls = [
        f"https://www.noff.gg/brawl-stars/res/img/brawlers/{image_slug(english_name)}.webp",
        api_brawler.get("imageUrl"),
        api_brawler.get("imageUrl2"),
    ]
    return [u for u in urls if u]


def from_api_brawler(api_brawler: dict) -> dict:
    en = title_case(api_brawler["name"])
    key = normalize_name(api_brawler["name"])
    return {
        "name": resolve_display_name(api_brawler["name"], en),
        "en": en,
        "color": (api_brawler.get("rarity") or {}).get("color") or "#4cc9f0",
        "image_urls": image_urls_for(api_brawler, en),
    }


def build_roster(api_brawlers: list[dict]) -> list[dict]:
    excluded = {normalize_name(n) for n in EXCLUDED_ENGLISH_NAMES}
    roster = [
        from_api_brawler(item)
        for item in api_brawlers
        if item.get("imageUrl")
    ]
    roster = [b for b in roster if normalize_name(b["en"]) not in excluded]

    for brawler in roster:
        brawler["name"] = resolve_display_name(brawler["en"], brawler["name"])

    existing = {normalize_name(b["en"]) for b in roster}
    for item in EXTRA_BRAWLERS:
        key = normalize_name(item["en"])
        if key not in existing and key not in excluded:
            roster.append(
                {
                    "name": item["name"],
                    "en": item["en"],
                    "color": item["color"],
                    "image_urls": list(item["image_urls"]),
                }
            )
            existing.add(key)
    return roster


def fetch_api_list() -> list[dict]:
    response = requests.get(settings.BRAWLAPI_URL, timeout=20)
    response.raise_for_status()
    data = response.json()
    return data.get("list") or []


def get_roster(*, force_refresh: bool = False) -> list[dict]:
    """Return cached roster; refresh from BrawlAPI when stale."""
    ttl = getattr(settings, "BRAWLER_CACHE_SECONDS", 1800)
    now = time.time()

    with _cache_lock:
        cached = _roster_cache["brawlers"]
        age = now - float(_roster_cache["fetched_at"] or 0)
        if cached is not None and not force_refresh and age < ttl:
            return [dict(b) for b in cached]

    api_list = fetch_api_list()
    roster = build_roster(api_list)

    with _cache_lock:
        _roster_cache["brawlers"] = roster
        _roster_cache["fetched_at"] = time.time()
        return [dict(b) for b in roster]


def find_brawler(roster: list[dict], en: str) -> dict | None:
    key = normalize_name(en)
    for brawler in roster:
        if normalize_name(brawler["en"]) == key:
            return brawler
    return None


def shuffle_copy(items: list) -> list:
    result = list(items)
    random.shuffle(result)
    return result


def make_question(roster: list[dict], deck: list[str]) -> tuple[dict, list[str], dict]:
    """
    Pop next answer from deck and build 4 choices.
    Returns (current_brawler, remaining_deck, public_question_payload).
    """
    if len(roster) < 4:
        raise ValueError("not_enough_brawlers")

    working_deck = list(deck)
    if not working_deck:
        working_deck = [b["en"] for b in shuffle_copy(roster)]

    current_en = working_deck.pop()
    current = find_brawler(roster, current_en)
    if current is None:
        # Stale deck entry — retry once with fresh deck
        working_deck = [b["en"] for b in shuffle_copy(roster)]
        current_en = working_deck.pop()
        current = find_brawler(roster, current_en)
        if current is None:
            raise ValueError("brawler_missing")

    distractors = shuffle_copy([b for b in roster if normalize_name(b["en"]) != normalize_name(current["en"])])
    options = shuffle_copy([current, *distractors[:3]])

    payload = {
        "options": [{"name": o["name"], "en": o["en"]} for o in options],
        "image_urls": list(current["image_urls"]),
        "color": current["color"],
    }
    return current, working_deck, payload
