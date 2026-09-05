"""クイズ名簿の読み出しと問題生成。

名簿のソース・オブ・トゥルースは DB の Character。
BrawlAPI の直接フェッチは sync_characters 管理コマンド側に移した。
"""
from __future__ import annotations

import random
import re

from .models import Character


class RosterNotReady(Exception):
    """有効な全身キャラが 4 体未満のとき。API は英語メッセージを返す。"""

    def __init__(self, count: int):
        self.count = count
        super().__init__(
            "Not enough quiz-ready characters "
            f"(need at least 4 with is_active=True and image_kind=full_body; found {count}). "
            "Run `python manage.py sync_characters`, then "
            "`python manage.py verify_character_images` and/or activate characters in Django Admin."
        )


def normalize_name(name: str) -> str:
    return str(name).strip().upper()


def name_override_keys(name: str) -> list[str]:
    """スペース / ハイフンの揺れを吸収して NAME_OVERRIDES を引く。"""
    n = normalize_name(name)
    variants = {n, n.replace(" ", "-"), n.replace("-", " ")}
    return list(variants)


def title_case(name: str) -> str:
    return re.sub(r"\b[a-z]", lambda m: m.group(0).upper(), str(name).lower())


def image_slug(name: str) -> str:
    """noff.gg 全身画像パス用スラッグ（旧 runtime と同じ規則）。"""
    from .characters_config import IMAGE_SLUG_OVERRIDES

    override = IMAGE_SLUG_OVERRIDES.get(normalize_name(name))
    if override:
        return override
    slug = name.lower().replace("&", "and").replace(".", "")
    slug = re.sub(r"\s+", "-", slug)
    return slug


def noff_full_body_url(english_name: str) -> str:
    """仮の全身候補 URL。存在確認は verify_character_images に任せる。"""
    return (
        "https://www.noff.gg/brawl-stars/res/img/brawlers/"
        f"{image_slug(english_name)}.webp"
    )


def is_noff_full_body_url(url: str) -> bool:
    """noff の brawlers/ パスなら全身候補として扱う。"""
    if not url:
        return False
    return "noff.gg/brawl-stars/res/img/brawlers/" in url


def character_to_roster_item(ch: Character) -> dict:
    """問題生成が期待する辞書形。image_url は単一（フォールバックなし）。"""
    return {
        "name": ch.display_name,
        "en": ch.name_en,
        "color": ch.color or "#4cc9f0",
        "image_url": ch.image_url,
    }


def get_roster(*, force_refresh: bool = False) -> list[dict]:
    """クイズ名簿: is_active + full_body のみ。

    force_refresh は旧 API キャッシュ互換の引数で、DB 読みでは無視する。
    """
    del force_refresh  # API キャッシュ時代のシグネチャ互換
    qs = Character.objects.filter(
        is_active=True,
        image_kind=Character.ImageKind.FULL_BODY,
    ).exclude(image_url="")
    return [character_to_roster_item(ch) for ch in qs]


def require_roster() -> list[dict]:
    """4 体未満なら RosterNotReady。views から呼ぶ。"""
    roster = get_roster()
    if len(roster) < 4:
        raise RosterNotReady(len(roster))
    return roster


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
    デッキから次の正解を取り、4 択を組み立てる。
    戻り値: (current_brawler, remaining_deck, public_question_payload)
    payload の画像は image_url 単一（旧 image_urls 配列は廃止）。
    """
    if len(roster) < 4:
        raise RosterNotReady(len(roster))

    working_deck = list(deck)
    if not working_deck:
        working_deck = [b["en"] for b in shuffle_copy(roster)]

    current_en = working_deck.pop()
    current = find_brawler(roster, current_en)
    if current is None:
        # デッキが古い名簿由来のとき、作り直して一度だけリトライ
        working_deck = [b["en"] for b in shuffle_copy(roster)]
        current_en = working_deck.pop()
        current = find_brawler(roster, current_en)
        if current is None:
            raise ValueError("brawler_missing")

    distractors = shuffle_copy(
        [b for b in roster if normalize_name(b["en"]) != normalize_name(current["en"])]
    )
    options = shuffle_copy([current, *distractors[:3]])

    payload = {
        "options": [{"name": o["name"], "en": o["en"]} for o in options],
        # 単一 URL。フロントもフォールバック連鎖しない。
        "image_url": current["image_url"],
        "color": current["color"],
    }
    return current, working_deck, payload
