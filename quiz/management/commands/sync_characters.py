"""BrawlAPI と EXTRA_BRAWLERS を Character テーブルへ同期する。

ルール（合意済み）:
- NEW: noff 全身候補 URL を仮置き、image_kind=unknown、is_active=False
- EXISTING: display_name / color / api_id のみ更新。
  image_url / image_kind / is_active は絶対に上書きしない（手動確定を守る）
- EXCLUDED_ENGLISH_NAMES は新規作成せず、既存があれば is_active=False
- EXTRA_BRAWLERS は source=extra で upsert（画像系フィールドは既存なら触らない）
"""
from __future__ import annotations

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from quiz.characters_config import (
    EXCLUDED_ENGLISH_NAMES,
    EXTRA_BRAWLERS,
    NAME_OVERRIDES,
)
from quiz.models import Character
from quiz.services import (
    name_override_keys,
    noff_full_body_url,
    normalize_name,
    title_case,
)


def resolve_display_name(api_name: str, fallback: str) -> str:
    for key in name_override_keys(api_name):
        if key in NAME_OVERRIDES:
            return NAME_OVERRIDES[key]
    return fallback


class Command(BaseCommand):
    help = (
        "Fetch BrawlAPI brawlers and upsert Character rows. "
        "New rows stay inactive until verified/activated."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print actions without writing to the database.",
        )

    def handle(self, *args, **options):
        dry = options["dry_run"]
        url = settings.BRAWLAPI_URL
        self.stdout.write(f"Fetching {url} …")
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        api_list = response.json().get("list") or []

        excluded = {normalize_name(n) for n in EXCLUDED_ENGLISH_NAMES}
        created = updated = skipped_excluded = 0

        for item in api_list:
            api_name = item.get("name") or ""
            en = title_case(api_name)
            key = normalize_name(en)

            if key in excluded:
                # 除外リスト: 名簿に載せない。既存があれば無効化のみ。
                skipped_excluded += 1
                existing = Character.objects.filter(name_en__iexact=en).first()
                if existing and existing.is_active and not dry:
                    existing.is_active = False
                    existing.save(update_fields=["is_active", "updated_at"])
                    self.stdout.write(f"  deactivated excluded: {en}")
                continue

            # imageUrl が無い API 行はスキップ（旧 build_roster と同じ）
            if not item.get("imageUrl"):
                continue

            display = resolve_display_name(api_name, en)
            color = (item.get("rarity") or {}).get("color") or "#4cc9f0"
            api_id = item.get("id")
            api_image = item.get("imageUrl") or ""
            provisional = noff_full_body_url(en)

            existing = Character.objects.filter(name_en__iexact=en).first()
            if existing:
                # 既存: メタデータのみ。画像・有効フラグは触らない。
                if not dry:
                    existing.display_name = display
                    existing.color = color
                    existing.api_id = api_id
                    # name_en はキー。表記ゆれがあれば正規化（通常は同じ）
                    if existing.name_en != en:
                        # unique 衝突を避けるため、別行が無ければだけ直す
                        conflict = (
                            Character.objects.filter(name_en=en)
                            .exclude(pk=existing.pk)
                            .exists()
                        )
                        if not conflict:
                            existing.name_en = en
                    # api portrait は予備欄のみ更新（クイズには使わない）
                    if api_image and not existing.api_image_url:
                        existing.api_image_url = api_image
                    existing.save()
                updated += 1
            else:
                if not dry:
                    Character.objects.create(
                        api_id=api_id,
                        name_en=en,
                        display_name=display,
                        color=color,
                        image_url=provisional,
                        api_image_url=api_image,
                        image_kind=Character.ImageKind.UNKNOWN,
                        is_active=False,
                        source=Character.Source.BRAWLAPI,
                    )
                created += 1
                self.stdout.write(f"  created (inactive): {en}")

        # extras: API に無い手動追加。source=extra。
        for item in EXTRA_BRAWLERS:
            en = item["en"]
            key = normalize_name(en)
            if key in excluded:
                continue
            urls = item.get("image_urls") or []
            image_url = urls[0] if urls else noff_full_body_url(en)
            existing = Character.objects.filter(name_en__iexact=en).first()
            if existing:
                if not dry:
                    existing.display_name = item.get("name") or en
                    existing.color = item.get("color") or existing.color
                    if existing.source != Character.Source.EXTRA:
                        existing.source = Character.Source.EXTRA
                    existing.save()
                updated += 1
            else:
                if not dry:
                    Character.objects.create(
                        api_id=None,
                        name_en=en,
                        display_name=item.get("name") or en,
                        color=item.get("color") or "#4cc9f0",
                        image_url=image_url,
                        image_kind=Character.ImageKind.UNKNOWN,
                        is_active=False,
                        source=Character.Source.EXTRA,
                    )
                created += 1
                self.stdout.write(f"  created extra (inactive): {en}")

        prefix = "[dry-run] " if dry else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix}sync done: created={created} updated={updated} "
                f"excluded_skipped={skipped_excluded}"
            )
        )
        self.stdout.write(
            "Note: new/updated rows stay inactive until verify_character_images "
            "or Admin activation (is_active + image_kind=full_body)."
        )
