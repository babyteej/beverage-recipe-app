"""Which beverage_types each ingredient may appear in, based on preparation form."""

from __future__ import annotations

import re
from typing import Any, TypedDict


class PreparationTransform(TypedDict):
    beverage_type: str
    stage: str
    hint: str
    prep_keywords: tuple[str, ...]


ALL_BEVERAGE_TYPES = frozenset({
    "cold_press_juice",
    "smoothie",
    "hot_tea",
    "cold_brew",
    "tonic",
    "infusion",
    "fermented",
    "decoction",
})

# Slugs with explicit allowlists (pending_review filename stems).
FORCE_ALLOWLIST: dict[str, frozenset[str]] = {
    "kratom-informational-only-schedule-per-region": frozenset({"hot_tea", "decoction", "cold_brew"}),
    "kombucha-scoby-culture-not-consumed-directly": frozenset({"fermented"}),
}

GLOBAL_EXCLUDE_NAME_PATTERNS = (
    re.compile(r"informational only", re.I),
    re.compile(r"not consumed directly", re.I),
    re.compile(r"\bscoby\b", re.I),
    re.compile(r"starter culture", re.I),
    re.compile(r"schedule per region", re.I),
)

POWDER_OR_PREPARED_PATTERNS = (
    re.compile(r"\bpowder\b", re.I),
    re.compile(r"\bisolate\b", re.I),
    re.compile(r"\bpeptide", re.I),
    re.compile(r"protein shake", re.I),
    re.compile(r"\bprepared\b", re.I),
    re.compile(r"spirulina", re.I),
    re.compile(r"\bmaca\b", re.I),
    re.compile(r"ashwagandha", re.I),
)

SMOOTHIE_ONLY_LIQUID_PATTERNS = (
    re.compile(r"protein", re.I),
    re.compile(r"\bmilk\b", re.I),
    re.compile(r"kefir", re.I),
    re.compile(r"collagen", re.I),
    re.compile(r"filtered water", re.I),
    re.compile(r"coconut water", re.I),
)

TONIC_LIQUID_PATTERNS = (
    re.compile(r"bone broth", re.I),
    re.compile(r"aloe vera", re.I),
    re.compile(r"beet juice", re.I),
    re.compile(r"cherry juice", re.I),
    re.compile(r"pomegranate juice", re.I),
    re.compile(r"green tea", re.I),
    re.compile(r"matcha", re.I),
)

# Bottled/prepared juices that may be stirred into cold-pressed juice at finish (not pressed).
FINISH_MIXIN_JUICE_PATTERNS = (
    re.compile(r"beet juice|beetroot juice", re.I),
    re.compile(r"tart cherry juice", re.I),
    re.compile(r"pomegranate juice", re.I),
    re.compile(r"aloe vera juice", re.I),
)

CATEGORY_BEVERAGE_TYPES: dict[str, frozenset[str]] = {
    "fruit": frozenset({"cold_press_juice", "smoothie", "tonic", "fermented", "infusion"}),
    "vegetable": frozenset({"cold_press_juice", "smoothie", "tonic", "decoction"}),
    "root": frozenset({"cold_press_juice", "smoothie", "hot_tea", "decoction", "infusion", "tonic", "cold_brew"}),
    "herb": frozenset({"hot_tea", "infusion", "cold_brew", "decoction", "smoothie", "tonic"}),
    "flower": frozenset({"hot_tea", "infusion", "cold_brew", "smoothie", "tonic"}),
    "mushroom": frozenset({"hot_tea", "decoction", "infusion", "tonic", "smoothie"}),
    "bark": frozenset({"decoction", "hot_tea", "infusion", "tonic", "smoothie"}),
    "seed": frozenset({"decoction", "smoothie", "tonic", "hot_tea", "infusion"}),
    "fermented_base": frozenset({"fermented", "smoothie", "tonic"}),
    "resin": frozenset({"tonic", "decoction"}),
    "mineral": frozenset(),
    "other": frozenset({"smoothie", "tonic", "hot_tea", "infusion", "cold_brew"}),
}

SUBCATEGORY_BEVERAGE_TYPES: dict[str, frozenset[str]] = {
    "liquid_base": frozenset({"smoothie", "tonic"}),
    "starter_culture": frozenset({"fermented"}),
    "scoby": frozenset({"fermented"}),
}


def _searchable_text(data: dict[str, Any], seed_name: str | None = None) -> str:
    parts = [
        seed_name or "",
        data.get("name") or "",
        data.get("subcategory") or "",
        data.get("personal_notes") or "",
        data.get("preparation_notes") or "",
        " ".join(data.get("aliases") or []),
    ]
    return " ".join(parts)


def _is_powder_or_prepared(text: str) -> bool:
    return any(p.search(text) for p in POWDER_OR_PREPARED_PATTERNS)


def _is_finish_mixin_juice(name: str) -> bool:
    return any(p.search(name) for p in FINISH_MIXIN_JUICE_PATTERNS)


def _is_protein_or_dairy_liquid(name: str) -> bool:
    return any(p.search(name) for p in SMOOTHIE_ONLY_LIQUID_PATTERNS)


def _liquid_base_types(name: str) -> frozenset[str]:
    """Prepared pourable bases — never cold-pressed; split smoothie vs tonic."""
    if _is_protein_or_dairy_liquid(name):
        return frozenset({"smoothie"})
    if any(p.search(name) for p in TONIC_LIQUID_PATTERNS):
        return frozenset({"smoothie", "tonic"})
    return frozenset({"smoothie"})


def compute_eligible_beverage_types(
    data: dict[str, Any],
    *,
    seed_name: str | None = None,
    slug: str | None = None,
) -> frozenset[str]:
    """Return beverage_types this ingredient may appear in without extra transformation."""
    text = _searchable_text(data, seed_name)

    if slug and slug in FORCE_ALLOWLIST:
        return FORCE_ALLOWLIST[slug]

    if re.search(r"kratom", text, re.I):
        return frozenset({"hot_tea", "decoction", "cold_brew"})

    for pattern in GLOBAL_EXCLUDE_NAME_PATTERNS:
        if pattern.search(text):
            return frozenset()

    subcategory = (data.get("subcategory") or "").lower()
    if subcategory in SUBCATEGORY_BEVERAGE_TYPES:
        eligible = set(SUBCATEGORY_BEVERAGE_TYPES[subcategory])
        if subcategory == "liquid_base":
            eligible = set(_liquid_base_types(data.get("name") or ""))
        return frozenset(eligible & ALL_BEVERAGE_TYPES)

    category = (data.get("category") or "other").lower()
    eligible = set(CATEGORY_BEVERAGE_TYPES.get(category, CATEGORY_BEVERAGE_TYPES["other"]))

    # Powders, prepared isolates, and microalgae powders — blend/steep/decoct, not cold-pressed.
    if _is_powder_or_prepared(text):
        eligible.discard("cold_press_juice")
        eligible.discard("fermented")

    # Resins are not fresh-pressed; bark spices may be ground into smoothies as finish.
    if category == "resin":
        eligible.discard("smoothie")
        eligible.discard("cold_press_juice")
    elif category == "bark":
        eligible.discard("cold_press_juice")

    # Delicate flowers/herbs — not typically decoction unless woody.
    if category in {"flower", "herb"} and subcategory not in {"root", "bark", "seed"}:
        eligible.discard("decoction")

    # Fresh produce is not fermented unless explicitly a fermented ingredient.
    if category in {"fruit", "vegetable"}:
        eligible.discard("fermented")

    return frozenset(eligible & ALL_BEVERAGE_TYPES)


def _ingredient_profile(data: dict[str, Any], seed_name: str | None = None) -> dict[str, Any]:
    text = _searchable_text(data, seed_name)
    return {
        "text": text,
        "category": (data.get("category") or "other").lower(),
        "subcategory": (data.get("subcategory") or "").lower(),
        "is_powder": _is_powder_or_prepared(text),
        "is_liquid_base": (data.get("subcategory") or "").lower() == "liquid_base",
        "is_honey_or_syrup": bool(re.search(r"\bhoney\b|syrup|molasses", text, re.I)),
        "is_fresh_produce": (data.get("category") or "").lower() in {"fruit", "vegetable", "root"},
    }


def compute_preparation_transforms(
    data: dict[str, Any],
    *,
    seed_name: str | None = None,
    slug: str | None = None,
) -> list[PreparationTransform]:
    """
    Ways to use this ingredient outside its default beverage_types.

    Each transform requires the recipe ingredient's `preparation` field to describe
    the transformation and the correct `stage`.
    """
    default = compute_eligible_beverage_types(data, seed_name=seed_name, slug=slug)
    if not default:
        return []

    profile = _ingredient_profile(data, seed_name)
    transforms: list[PreparationTransform] = []

    def add(bt: str, stage: str, hint: str, keywords: tuple[str, ...]) -> None:
        if bt in default or bt not in ALL_BEVERAGE_TYPES:
            return
        transforms.append(
            PreparationTransform(
                beverage_type=bt,
                stage=stage,
                hint=hint,
                prep_keywords=keywords,
            )
        )

    if profile["is_liquid_base"]:
        name = data.get("name") or ""
        if _is_finish_mixin_juice(name) and not _is_protein_or_dairy_liquid(name):
            add(
                "cold_press_juice",
                "finish",
                "Stir prepared juice into cold-pressed juice after extraction — do not put through the juicer",
                ("stir", "mix", "blend in", "after press", "finish", "juice"),
            )
        return transforms

    if profile["is_powder"]:
        add(
            "smoothie",
            "blend",
            "Dissolve or blend powder into the liquid base before or during blending",
            ("powder", "dissolve", "blend", "whisk", "mix"),
        )
        add(
            "hot_tea",
            "steep",
            "Whisk or steep powder in hot water",
            ("powder", "steep", "whisk", "dissolve", "infuse"),
        )
        add(
            "infusion",
            "steep",
            "Steep or whisk powder in water",
            ("powder", "steep", "whisk", "dissolve", "infuse"),
        )
        add(
            "cold_brew",
            "steep",
            "Cold-steep powder in water",
            ("powder", "cold steep", "steep", "dissolve", "infuse"),
        )
        add(
            "decoction",
            "steep",
            "Simmer powder in water and reduce",
            ("powder", "simmer", "decoct", "boil"),
        )
        add(
            "tonic",
            "finish",
            "Stir powder into the finished tonic",
            ("powder", "stir", "dissolve", "whisk", "mix"),
        )
        add(
            "cold_press_juice",
            "finish",
            "Stir or whisk powder into juice after pressing — never put dry powder through the juicer",
            ("powder", "stir", "whisk", "dissolve", "after press", "finish"),
        )

    if profile["is_honey_or_syrup"]:
        add(
            "cold_press_juice",
            "finish",
            "Stir honey or syrup into pressed juice after extraction",
            ("stir", "dissolve", "mix", "honey", "syrup", "finish", "after press"),
        )

    if profile["category"] in {"herb", "flower", "mushroom"} and "smoothie" not in default:
        add(
            "smoothie",
            "liquid_base",
            "Brew a strong infusion, cool, and use as the smoothie liquid base (100–150ml)",
            ("infusion", "brew", "steep", "cool", "liquid base", "concentrated"),
        )
        add(
            "smoothie",
            "blend",
            "Blend fresh or rehydrated leaves into the smoothie",
            ("blend", "fresh", "leaves", "chop"),
        )

    if profile["is_fresh_produce"] and "hot_tea" not in default:
        add(
            "hot_tea",
            "steep",
            "Slice and steep fresh produce in hot water (unusual — use sparingly)",
            ("steep", "slice", "simmer", "fresh"),
        )

    if profile["category"] in {"root", "bark", "seed", "mushroom"} and "smoothie" not in default:
        add(
            "smoothie",
            "blend",
            "Use finely grated fresh root or a cooled decoction blended in (small amount)",
            ("grate", "decoct", "cool", "blend", "simmer"),
        )

    return transforms


def get_transforms_for_beverage_type(
    data: dict[str, Any],
    beverage_type: str,
    *,
    seed_name: str | None = None,
    slug: str | None = None,
) -> list[PreparationTransform]:
    if beverage_type in compute_eligible_beverage_types(data, seed_name=seed_name, slug=slug):
        return []
    return [t for t in compute_preparation_transforms(data, seed_name=seed_name, slug=slug) if t["beverage_type"] == beverage_type]


def compute_reachable_beverage_types(
    data: dict[str, Any],
    *,
    seed_name: str | None = None,
    slug: str | None = None,
) -> frozenset[str]:
    """Default types plus types reachable via a documented preparation transform."""
    reachable = set(compute_eligible_beverage_types(data, seed_name=seed_name, slug=slug))
    for transform in compute_preparation_transforms(data, seed_name=seed_name, slug=slug):
        reachable.add(transform["beverage_type"])
    return frozenset(reachable & ALL_BEVERAGE_TYPES)


def validate_ingredient_usage(
    data: dict[str, Any],
    beverage_type: str,
    ingredient_line: dict[str, Any],
    *,
    seed_name: str | None = None,
    slug: str | None = None,
) -> str | None:
    """
    Return an error message if this ingredient cannot be used this way; else None.
    """
    name = data.get("name") or "ingredient"
    stage = str(ingredient_line.get("stage") or "")
    preparation = str(ingredient_line.get("preparation") or "").lower()

    if beverage_type in compute_eligible_beverage_types(data, seed_name=seed_name, slug=slug):
        return None

    transforms = get_transforms_for_beverage_type(
        data, beverage_type, seed_name=seed_name, slug=slug
    )
    if not transforms:
        return ineligibility_notes(data, beverage_type, seed_name=seed_name, slug=slug) or (
            f"{name} cannot be used for {beverage_type}"
        )

    for transform in transforms:
        if stage != transform["stage"]:
            continue
        if any(keyword in preparation for keyword in transform["prep_keywords"]):
            return None

    hints = "; ".join(f"stage={t['stage']}: {t['hint']}" for t in transforms)
    return (
        f"{name} requires a preparation transform for {beverage_type}. "
        f"Set preparation to describe the transform. Options: {hints}"
    )


def is_usable_for_beverage_type(
    data: dict[str, Any],
    beverage_type: str,
    *,
    seed_name: str | None = None,
    slug: str | None = None,
) -> bool:
    """True if default-eligible or at least one preparation transform exists."""
    if beverage_type in compute_eligible_beverage_types(data, seed_name=seed_name, slug=slug):
        return True
    return bool(get_transforms_for_beverage_type(data, beverage_type, seed_name=seed_name, slug=slug))


def validate_anchors_for_beverage_type(
    anchors: list[dict[str, Any]],
    beverage_type: str,
) -> list[dict[str, str]]:
    """Return conflicts for anchors that cannot be used with this beverage type at all."""
    conflicts: list[dict[str, str]] = []
    for anchor in anchors:
        name = anchor.get("name") or "Unknown"
        if is_usable_for_beverage_type(anchor, beverage_type):
            continue
        sub = anchor.get("subcategory") or ""
        if sub == "liquid_base" and _is_protein_or_dairy_liquid(name):
            suggestion = (
                f"{name} is a prepared protein/dairy liquid for smoothies only. "
                "Remove it as an anchor, choose beverage type 'smoothie', or anchor a powder "
                "you will dissolve (not a pre-made shake)."
            )
        elif sub == "liquid_base":
            suggestion = (
                f"{name} is a prepared liquid base. It cannot be used with {beverage_type}. "
                "Pick fresh produce to press, or change the beverage type."
            )
        elif beverage_type == "cold_press_juice":
            suggestion = (
                f"{name} cannot be cold-pressed in its default form. "
                "Use fresh produce anchors, or a powder with a finish-stage transform."
            )
        else:
            suggestion = (
                f"Remove {name} as an anchor or choose a different beverage type."
            )
        conflicts.append(
            {
                "ingredient": name,
                "reason": ineligibility_notes(anchor, beverage_type) or (
                    f"{name} is not compatible with {beverage_type}"
                ),
                "suggestion": suggestion,
            }
        )
    return conflicts


def ineligibility_notes(
    data: dict[str, Any],
    beverage_type: str,
    *,
    seed_name: str | None = None,
    slug: str | None = None,
) -> str | None:
    """Why an ingredient cannot be used for a beverage type, if applicable."""
    eligible = compute_eligible_beverage_types(data, seed_name=seed_name, slug=slug)
    if beverage_type in eligible:
        return None
    name = data.get("name") or "ingredient"
    sub = data.get("subcategory") or ""
    if sub == "liquid_base":
        return f"{name} is a prepared liquid base (subcategory liquid_base) — use in smoothies, not {beverage_type}"
    if _is_powder_or_prepared(_searchable_text(data, seed_name)):
        return f"{name} is a powder or prepared form — not cold-pressable; use in blend/steep/decoction contexts"
    return f"{name} is not eligible for {beverage_type} in its default preparation form"


def normalize_beverage_types(
    data: dict[str, Any],
    *,
    seed_name: str | None = None,
    slug: str | None = None,
) -> dict[str, Any]:
    """Replace beverage_types with the computed eligible set."""
    data["beverage_types"] = sorted(compute_eligible_beverage_types(data, seed_name=seed_name, slug=slug))
    return data


# Backward-compatible smoothie helpers
def is_smoothie_eligible(
    data: dict[str, Any],
    *,
    seed_name: str | None = None,
    slug: str | None = None,
) -> bool:
    return "smoothie" in compute_eligible_beverage_types(data, seed_name=seed_name, slug=slug)


def normalize_smoothie_beverage_types(
    data: dict[str, Any],
    *,
    seed_name: str | None = None,
    slug: str | None = None,
) -> dict[str, Any]:
    return normalize_beverage_types(data, seed_name=seed_name, slug=slug)
