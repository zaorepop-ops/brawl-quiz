"""Brawler roster config — exclusions, extras, and image slug overrides.

Display names use English (`en`). NAME_OVERRIDES is intentionally empty so
answer choices and reveals show English brawler names. Keep IMAGE_SLUG_OVERRIDES,
EXCLUDED_ENGLISH_NAMES, and EXTRA_BRAWLERS for data correctness.
"""

EXCLUDED_ENGLISH_NAMES = [
    "Buzz-Lightyear",
]

# Intentionally empty: UI displays English names instead of localized overrides.
NAME_OVERRIDES = {}

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

IMAGE_SLUG_OVERRIDES = {
    "8-BIT": "8_bit",
    "EL-PRIMO": "el_primo",
    "JAE-YONG": "jae_yong",
    "LARRY-LAWRIE": "larry_and_lawrie",
    "MR-P": "mr_p",
    "R-T": "r_t",
}
