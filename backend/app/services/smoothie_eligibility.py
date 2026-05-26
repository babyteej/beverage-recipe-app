"""Backward-compatible re-exports — use beverage_type_eligibility for new code."""

from app.services.beverage_type_eligibility import (  # noqa: F401
    compute_eligible_beverage_types,
    ineligibility_notes,
    is_smoothie_eligible,
    normalize_beverage_types,
    normalize_smoothie_beverage_types,
)

SMOOTHIE_FORCE_EXCLUDE_SLUGS = frozenset({
    "kratom-informational-only-schedule-per-region",
    "kombucha-scoby-culture-not-consumed-directly",
})


def smoothie_ineligibility_reason(
    data: dict,
    *,
    seed_name: str | None = None,
    slug: str | None = None,
) -> str | None:
    return ineligibility_notes(data, "smoothie", seed_name=seed_name, slug=slug)
