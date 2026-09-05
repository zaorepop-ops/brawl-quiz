"""同期用の静的設定（名簿そのものは DB の Character）。

- EXCLUDED_ENGLISH_NAMES: sync で新規作成しない / 既存は無効化
- EXTRA_BRAWLERS: API に無いキャラを source=extra で投入
- IMAGE_SLUG_OVERRIDES: noff.gg 全身 URL のスラッグ例外
- NAME_OVERRIDES: 表示名上書き（空なら英語のまま）
"""

# sync_characters がスキップ / 無効化する英語名
EXCLUDED_ENGLISH_NAMES = [
    "Buzz-Lightyear",
]

# 意図的に空: UI は英語名を表示する
NAME_OVERRIDES = {}

# API にまだ無い（または別管理したい）ブロスタ。sync で source=extra。
EXTRA_BRAWLERS = [
    {
        "name": "Sirius",
        "en": "Sirius",
        "color": "#fff36b",
        "image_urls": [
            "https://www.noff.gg/brawl-stars/res/img/brawlers/sirius.webp",
        ],
    },
    {
        "name": "Damian",
        "en": "Damian",
        "color": "#fe5e72",
        "image_urls": [
            "https://www.noff.gg/brawl-stars/res/img/brawlers/damian.webp",
        ],
    },
    {
        "name": "Najia",
        "en": "Najia",
        "color": "#fe5e72",
        "image_urls": [
            "https://www.noff.gg/brawl-stars/res/img/brawlers/najia.webp",
        ],
    },
    {
        "name": "Starr-Nova",
        "en": "Starr-Nova",
        "color": "#fe5e72",
        "image_urls": [
            "https://www.noff.gg/brawl-stars/res/img/brawlers/starr_nova.webp",
        ],
    },
]

# ハイフン名などを noff のファイル名（アンダースコア等）に合わせる
IMAGE_SLUG_OVERRIDES = {
    "8-BIT": "8_bit",
    "EL-PRIMO": "el_primo",
    "JAE-YONG": "jae_yong",
    "LARRY-LAWRIE": "larry_and_lawrie",
    "MR-P": "mr_p",
    "R-T": "r_t",
}
