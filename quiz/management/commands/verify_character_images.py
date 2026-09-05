"""仮置き image_url の HTTP 到達性を確認し、種別 / 有効化を更新する。

方針:
- 対象: is_active=False または image_kind=unknown（確定済み行は触らない）
- HTTP 200 なら image_kind=full_body
- is_active は noff 全身パスのときだけ True（初回セットアップを実用的にする）
  それ以外の 200 は full_body にするが is_active は False のまま（人の確認待ち）
"""
from __future__ import annotations

import requests
from django.core.management.base import BaseCommand
from django.db.models import Q

from quiz.models import Character
from quiz.services import is_noff_full_body_url


class Command(BaseCommand):
    help = (
        "HEAD/GET image_url for inactive/unknown characters; "
        "set image_kind=full_body on HTTP 200; activate only noff full-body URLs."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print results without saving.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Max rows to check (0 = all).",
        )
        parser.add_argument(
            "--timeout",
            type=float,
            default=8.0,
            help="Per-request timeout seconds.",
        )

    def handle(self, *args, **options):
        dry = options["dry_run"]
        timeout = options["timeout"]
        # 確定済み（active + full_body）はスキップ。未確定だけ検査。
        qs = Character.objects.filter(
            Q(is_active=False) | Q(image_kind=Character.ImageKind.UNKNOWN)
        ).exclude(image_url="")
        qs = qs.order_by("name_en")
        if options["limit"]:
            qs = qs[: options["limit"]]

        ok = fail = activated = kinded = 0
        session = requests.Session()
        headers = {"User-Agent": "brawl-quiz-verify/1.0"}

        for ch in qs:
            url = ch.image_url
            status = self._probe(session, url, timeout, headers)
            if status == 200:
                ok += 1
                new_kind = Character.ImageKind.FULL_BODY
                # noff 全身パスなら初回利用のため有効化も許可
                new_active = is_noff_full_body_url(url)
                changed = []
                if ch.image_kind != new_kind:
                    ch.image_kind = new_kind
                    changed.append("image_kind=full_body")
                    kinded += 1
                if new_active and not ch.is_active:
                    ch.is_active = True
                    changed.append("is_active=True")
                    activated += 1
                if changed and not dry:
                    ch.save(update_fields=["image_kind", "is_active", "updated_at"])
                self.stdout.write(
                    f"  OK {status} {ch.name_en}: {', '.join(changed) or 'no change'} ({url})"
                )
            else:
                fail += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"  FAIL {status} {ch.name_en}: {url}"
                    )
                )

        prefix = "[dry-run] " if dry else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix}verify done: http200={ok} fail={fail} "
                f"set_full_body={kinded} activated={activated}"
            )
        )
        ready = Character.objects.filter(
            is_active=True, image_kind=Character.ImageKind.FULL_BODY
        ).count()
        self.stdout.write(f"Quiz-ready characters now: {ready}")

    def _probe(self, session, url: str, timeout: float, headers: dict) -> int:
        """HEAD を試し、拒否されたら GET（一部 CDN は HEAD 非対応）。"""
        try:
            r = session.head(url, timeout=timeout, allow_redirects=True, headers=headers)
            if r.status_code in (405, 403, 400) or r.status_code >= 500:
                r = session.get(
                    url, timeout=timeout, allow_redirects=True, headers=headers, stream=True
                )
                r.close()
            return r.status_code
        except requests.RequestException:
            return 0
