"""Character の Django Admin。

運用フロー: sync → verify（任意）→ Admin で image_url / image_kind / is_active を確定。
"""
from django.contrib import admin

from .models import Character


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    # list で有効化状態と画像種別をすぐ確認できるようにする
    list_display = (
        "name_en",
        "display_name",
        "image_kind",
        "is_active",
        "source",
        "api_id",
        "updated_at",
    )
    list_filter = ("is_active", "image_kind", "source")
    search_fields = ("name_en", "display_name")
    # 手動キュレーション対象を先頭に
    list_editable = ("is_active", "image_kind")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name_en",
                    "display_name",
                    "api_id",
                    "color",
                    "source",
                )
            },
        ),
        (
            "Image / quiz readiness",
            {
                "description": (
                    "クイズに出すのは is_active=True かつ image_kind=full_body のみ。"
                    " sync_characters は既存行の image_url / image_kind / is_active を上書きしない。"
                ),
                "fields": (
                    "image_url",
                    "api_image_url",
                    "image_kind",
                    "is_active",
                ),
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at")},
        ),
    )
