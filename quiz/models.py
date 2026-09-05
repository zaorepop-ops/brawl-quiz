"""キャラクター（ブロスタ）の永続化モデル。

画像は URL のみ保持する（メディアファイルはまだ扱わない）。
クイズに出すのは is_active=True かつ image_kind=full_body のみ。
"""
from django.db import models


class Character(models.Model):
    """クイズ用ブロスタ1体分のマスタ。

    sync_characters が BrawlAPI / extras から投入し、
    Admin または verify_character_images で image / 有効化を確定する。
    """

    class ImageKind(models.TextChoices):
        # 全身イラストのみクイズ向け。ポートレートは誤答しやすいので除外。
        FULL_BODY = "full_body", "Full body"
        PORTRAIT = "portrait", "Portrait"
        UNKNOWN = "unknown", "Unknown"

    class Source(models.TextChoices):
        BRAWLAPI = "brawlapi", "BrawlAPI"
        MANUAL = "manual", "Manual"
        # characters_config.EXTRA_BRAWLERS 由来（API に無い手動追加）
        EXTRA = "extra", "Extra"

    # BrawlAPI の数値 ID。手動 extras は null のまま。
    api_id = models.IntegerField(null=True, blank=True, db_index=True)

    # 一意キー。英語名（title-case）で照合する。
    name_en = models.CharField(max_length=100, unique=True)

    # UI / 選択肢に出す表示名（現状は英語。将来ローカライズ可）。
    display_name = models.CharField(max_length=100)

    color = models.CharField(max_length=32, default="#4cc9f0")

    # クイズに使う単一画像 URL（ランタイムのフォールバック連鎖はしない）。
    image_url = models.URLField(max_length=500, blank=True)

    # API の portrait 等。クイズには使わず、確認用の予備。
    api_image_url = models.URLField(max_length=500, blank=True)

    image_kind = models.CharField(
        max_length=20,
        choices=ImageKind.choices,
        default=ImageKind.UNKNOWN,
    )

    # False のままならクイズ名簿に出ない。Admin または verify で有効化。
    is_active = models.BooleanField(default=False)

    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.BRAWLAPI,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name_en"]
        verbose_name = "Character"
        verbose_name_plural = "Characters"

    def __str__(self) -> str:
        return f"{self.display_name} ({self.name_en})"

    @property
    def quiz_ready(self) -> bool:
        """クイズ名簿に載せる条件（full_body + active）。"""
        return self.is_active and self.image_kind == self.ImageKind.FULL_BODY
