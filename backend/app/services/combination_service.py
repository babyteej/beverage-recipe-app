"""Three-stage combination engine: candidate selection → AI composition → validation."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from supabase import Client

from app.models.api import (
    CombinationConstraints,
    CombinationSuggestRequest,
    CombinationSuggestResponse,
    SuggestedFormulation,
)
from app.services.anthropic_service import AnthropicService, get_combination_model_name
from app.services.beverage_type_eligibility import (
    compute_eligible_beverage_types,
    get_transforms_for_beverage_type,
    validate_anchors_for_beverage_type,
    validate_ingredient_usage,
)
from app.services.ingredient_service import fetch_ingredient, list_ingredients, list_liquid_base_ingredients

PROMPT_FILE = Path(__file__).resolve().parent.parent.parent / "prompts" / "combination_reasoning.txt"
MIN_CANDIDATES = 5
TARGET_POOL_SIZE = 12
MIN_LIQUID_BASES_IN_POOL = 3


def _ensure_smoothie_liquid_bases(
    client: Client,
    pool: list[dict[str, Any]],
    *,
    include_unverified: bool,
) -> list[dict[str, Any]]:
    """When composing smoothies, always include liquid_base options in the candidate pool."""
    liquid_bases = list_liquid_base_ingredients(client, include_unverified=include_unverified)
    if not liquid_bases:
        return pool

    by_id = {str(i["id"]): i for i in pool}
    for base in liquid_bases:
        by_id[str(base["id"])] = base

    merged = list(by_id.values())
    bases_in_pool = [i for i in merged if i.get("subcategory") == "liquid_base"]
    if len(bases_in_pool) >= MIN_LIQUID_BASES_IN_POOL:
        return merged

    present_base_ids = {str(i["id"]) for i in bases_in_pool}
    for base in liquid_bases:
        bid = str(base["id"])
        if bid not in present_base_ids:
            merged.insert(0, base)
            present_base_ids.add(bid)
        if len(present_base_ids) >= MIN_LIQUID_BASES_IN_POOL:
            break
    return merged


def _eligible_pool(
    client: Client,
    *,
    include_unverified: bool,
    constraints: CombinationConstraints,
) -> list[dict[str, Any]]:
    if constraints.beverage_type:
        default_pool = list_ingredients(
            client,
            beverage_type=constraints.beverage_type,
            include_unverified=include_unverified,
        )
        by_id = {str(i["id"]): i for i in default_pool}
        # Include ingredients reachable via a documented preparation transform.
        for item in list_ingredients(client, include_unverified=include_unverified):
            iid = str(item["id"])
            if iid in by_id:
                continue
            if get_transforms_for_beverage_type(item, constraints.beverage_type):
                by_id[iid] = item
        pool = list(by_id.values())
    else:
        pool = list_ingredients(
            client,
            include_unverified=include_unverified,
        )

    exclude = {str(i) for i in constraints.exclude_ingredients}
    return [i for i in pool if str(i["id"]) not in exclude]


def _has_contraindication(candidate: dict[str, Any], against_names: set[str]) -> bool:
    contra = {c.lower() for c in candidate.get("combination_contraindications") or []}
    return bool(contra.intersection({n.lower() for n in against_names}))


def _terpene_score(a: dict[str, Any], b: dict[str, Any]) -> int:
    score = 0
    if a.get("primary_terpene") and a["primary_terpene"] == b.get("primary_terpene"):
        score += 3
    a_secondary = set(a.get("secondary_terpenes") or [])
    b_secondary = set(b.get("secondary_terpenes") or [])
    if a_secondary & b_secondary:
        score += 2
    if a.get("primary_terpene") in b_secondary or b.get("primary_terpene") in a_secondary:
        score += 1
    return score


def _overlap_score(a: dict[str, Any], b: dict[str, Any]) -> int:
    score = 0
    if set(a.get("body_systems") or []) & set(b.get("body_systems") or []):
        score += 2
    if set(a.get("beverage_types") or []) & set(b.get("beverage_types") or []):
        score += 2
    return score


def select_candidates_anchor(
    client: Client,
    anchor_ids: list[UUID],
    *,
    include_unverified: bool,
    constraints: CombinationConstraints,
) -> list[dict[str, Any]]:
    anchors = []
    for aid in anchor_ids:
        row = fetch_ingredient(client, aid)
        if not row:
            raise HTTPException(status_code=404, detail=f"Anchor ingredient not found: {aid}")
        anchors.append(row)

    pool = _eligible_pool(client, include_unverified=include_unverified, constraints=constraints)
    anchor_ids_str = {str(a["id"]) for a in anchors}
    anchor_names = {a["name"] for a in anchors}

    scored: list[tuple[int, dict[str, Any]]] = []
    for candidate in pool:
        cid = str(candidate["id"])
        if cid in anchor_ids_str:
            scored.append((1000, candidate))
            continue
        if _has_contraindication(candidate, anchor_names):
            continue
        for anchor in anchors:
            if _has_contraindication(anchor, {candidate["name"]}):
                continue
        score = 0
        for anchor in anchors:
            score += _terpene_score(candidate, anchor)
            score += _overlap_score(candidate, anchor)
        if score > 0:
            scored.append((score, candidate))

    scored.sort(key=lambda x: (-x[0], x[1]["name"].lower()))
    selected = [item for _, item in scored[:TARGET_POOL_SIZE]]

    # Ensure all anchors present
    present = {str(i["id"]) for i in selected}
    for anchor in anchors:
        if str(anchor["id"]) not in present:
            selected.insert(0, anchor)

    if constraints.beverage_type == "smoothie":
        selected = _ensure_smoothie_liquid_bases(
            client, selected, include_unverified=include_unverified
        )

    return selected


# Maps goal keywords to related terms found in claims, body systems, and categories.
GOAL_EXPANSIONS: dict[str, list[str]] = {
    "fiber": ["fiber", "fibre", "roughage", "regularity", "bowel", "motility", "prebiotic", "constipation", "laxative"],
    "fibre": ["fiber", "fibre", "roughage", "regularity", "bowel", "motility", "prebiotic"],
    "digestive": ["digest", "gut", "stomach", "carminative", "bloat", "nausea", "intestinal"],
    "digestion": ["digest", "gut", "stomach", "carminative", "bloat", "intestinal"],
    "gut": ["gut", "digest", "microbiome", "intestinal", "motility", "flora"],
    "anti": ["anti-inflammatory", "inflammation", "inflammatory"],
    "inflammatory": ["anti-inflammatory", "inflammation", "inflammatory"],
    "inflammation": ["anti-inflammatory", "inflammation", "inflammatory"],
    "sleep": ["sleep", "insomnia", "sedative", "nervous_system", "relax", "calm"],
    "energy": ["energy", "fatigue", "stimulant", "adaptogen", "vitality"],
    "immune": ["immune", "immunity", "antioxidant", "infection", "cold"],
    "detox": ["liver", "detox", "cleanse", "hepatic", "lymphatic"],
    "calm": ["calm", "anxiety", "stress", "nervous_system", "relax", "sedative"],
    "nervous": ["nervous_system", "nervous", "stress", "anxiety", "calm"],
}

GOAL_STOP_WORDS = frozenset({
    "a", "an", "the", "for", "and", "or", "with", "high", "low", "more", "less",
    "support", "health", "drink", "beverage", "juice", "tea", "make", "me", "my",
})

# Category boosts when goal tokens suggest these use cases.
GOAL_CATEGORY_BOOSTS: dict[str, list[str]] = {
    "fiber": ["vegetable", "fruit", "seed", "root"],
    "fibre": ["vegetable", "fruit", "seed", "root"],
    "digestive": ["root", "herb", "vegetable", "seed"],
    "gut": ["root", "herb", "vegetable", "seed"],
    "immune": ["herb", "mushroom", "fruit", "root"],
    "sleep": ["herb", "flower", "root"],
    "energy": ["root", "herb", "fruit"],
}


def _tokenize_goals(goals: list[str]) -> list[str]:
    tokens: set[str] = set()
    for goal in goals:
        for word in re.split(r"[\s,/\-]+", goal.lower()):
            word = word.strip()
            if word and len(word) > 2 and word not in GOAL_STOP_WORDS:
                tokens.add(word)
    expanded = set(tokens)
    for token in list(tokens):
        if token in GOAL_EXPANSIONS:
            expanded.update(GOAL_EXPANSIONS[token])
    return sorted(expanded)


def _text_contains_token(text: str, tokens: list[str]) -> bool:
    text_lower = text.lower()
    return any(t in text_lower for t in tokens)


def _goal_match_score(ingredient: dict[str, Any], goals: list[str]) -> int:
    tokens = _tokenize_goals(goals)
    if not tokens:
        return 0

    score = 0
    name_lower = (ingredient.get("name") or "").lower()
    category = ingredient.get("category") or ""

    for system in ingredient.get("body_systems") or []:
        system_text = system.replace("_", " ").lower()
        if _text_contains_token(system_text, tokens) or system.lower() in tokens:
            score += 3

    hp = ingredient.get("health_properties") or {}
    for claim in hp.get("traditional_claims") or []:
        claim_text = claim.get("claim", "")
        if _text_contains_token(claim_text, tokens):
            score += 2
        if _text_contains_token(claim.get("tradition", ""), tokens):
            score += 1

    for claim in hp.get("evidence_based_claims") or []:
        if _text_contains_token(claim.get("claim", ""), tokens):
            score += 2

    if _text_contains_token(name_lower, tokens):
        score += 2

    subcategory = (ingredient.get("subcategory") or "").lower()
    if subcategory and _text_contains_token(subcategory, tokens):
        score += 1

    for token in tokens:
        boosts = GOAL_CATEGORY_BOOSTS.get(token, [])
        if category in boosts:
            score += 2

    # Whole-goal phrase match (e.g. "gut health" in a claim)
    goal_phrase = " ".join(goals).lower()
    searchable = name_lower + " " + subcategory
    for claim in hp.get("traditional_claims", []) + hp.get("evidence_based_claims", []):
        searchable += " " + claim.get("claim", "")
    if len(goal_phrase) > 4 and goal_phrase in searchable.lower():
        score += 4

    return score


def select_candidates_goal(
    client: Client,
    health_goals: list[str],
    *,
    include_unverified: bool,
    constraints: CombinationConstraints,
) -> list[dict[str, Any]]:
    pool = _eligible_pool(client, include_unverified=include_unverified, constraints=constraints)
    scored = [( _goal_match_score(item, health_goals), item) for item in pool]
    scored.sort(key=lambda x: (-x[0], x[1]["name"].lower()))

    # Prefer ingredients with any relevance; if too few, pad with highest-scoring pool members
    positive = [item for s, item in scored if s > 0]
    if len(positive) >= MIN_CANDIDATES:
        selected = positive[:TARGET_POOL_SIZE]
    else:
        # Fallback: include zero-score items from fiber/gut-relevant categories when goals suggest that
        tokens = _tokenize_goals(health_goals)
        fallback_categories: set[str] = set()
        for token in tokens:
            fallback_categories.update(GOAL_CATEGORY_BOOSTS.get(token, []))

        fallback: list[dict[str, Any]] = list(positive)
        seen = {str(i["id"]) for i in fallback}
        for _, item in scored:
            if len(fallback) >= TARGET_POOL_SIZE:
                break
            iid = str(item["id"])
            if iid in seen:
                continue
            if fallback_categories and item.get("category") in fallback_categories:
                fallback.append(item)
                seen.add(iid)

        # Last resort: fill from full pool to reach MIN_CANDIDATES
        for _, item in scored:
            if len(fallback) >= max(MIN_CANDIDATES, TARGET_POOL_SIZE):
                break
            iid = str(item["id"])
            if iid not in seen:
                fallback.append(item)
                seen.add(iid)

        selected = fallback[:TARGET_POOL_SIZE]

    if constraints.beverage_type == "smoothie":
        selected = _ensure_smoothie_liquid_bases(
            client, selected, include_unverified=include_unverified
        )

    return selected


def _slim_candidate(
    ingredient: dict[str, Any],
    *,
    target_beverage_type: str | None = None,
) -> dict[str, Any]:
    slim: dict[str, Any] = {
        "ingredient_id": str(ingredient["id"]),
        "name": ingredient["name"],
        "category": ingredient["category"],
        "subcategory": ingredient.get("subcategory"),
        "primary_terpene": ingredient.get("primary_terpene"),
        "secondary_terpenes": ingredient.get("secondary_terpenes") or [],
        "flavour_profile": ingredient.get("flavour_profile") or [],
        "body_systems": ingredient.get("body_systems") or [],
        "beverage_types": ingredient.get("beverage_types") or [],
        "default_beverage_types": sorted(compute_eligible_beverage_types(ingredient)),
        "contraindications": ingredient.get("contraindications") or [],
        "combination_contraindications": ingredient.get("combination_contraindications") or [],
        "bioavailability_notes": ingredient.get("bioavailability_notes"),
        "preparation_notes": ingredient.get("preparation_notes"),
        "ratio_guidance": ingredient.get("ratio_guidance"),
        "verification_status": ingredient.get("verification_status"),
    }
    if target_beverage_type:
        transforms = get_transforms_for_beverage_type(ingredient, target_beverage_type)
        if transforms:
            slim["transform_options"] = [
                {
                    "stage": t["stage"],
                    "hint": t["hint"],
                    "preparation_must_describe": list(t["prep_keywords"][:4]),
                }
                for t in transforms
            ]
    return slim


def _build_prompt(
    request: CombinationSuggestRequest,
    candidates: list[dict[str, Any]],
    anchors: list[dict[str, Any]] | None = None,
) -> str:
    template = PROMPT_FILE.read_text(encoding="utf-8")
    constraints_json = json.dumps(request.constraints.model_dump(mode="json"), indent=2)
    target_bt = request.constraints.beverage_type
    pool_json = json.dumps(
        [_slim_candidate(c, target_beverage_type=target_bt) for c in candidates],
        indent=2,
    )

    if request.mode == "anchor":
        anchor_section = (
            "ANCHOR INGREDIENT(S) — MUST appear in every formulation:\n"
            + json.dumps(
                [_slim_candidate(a, target_beverage_type=target_bt) for a in (anchors or [])],
                indent=2,
            )
        )
    else:
        anchor_section = (
            "HEALTH GOALS — select ingredients that best serve these goals:\n"
            + json.dumps(request.health_goals or [], indent=2)
        )

    prompt = (
        template.replace("{{MODE}}", request.mode)
        .replace("{{CONSTRAINTS_JSON}}", constraints_json)
        .replace("{{ANCHOR_OR_GOAL_SECTION}}", anchor_section)
        .replace("{{CANDIDATE_POOL_JSON}}", pool_json)
    )
    constraints = request.constraints
    if constraints.beverage_type == "smoothie":
        prompt += (
            "\n\nCONSTRAINT OVERRIDE: beverage_type is smoothie. "
            "Apply SMOOTHIE RULES strictly — include liquid_base (ml) + blend (g) stages, "
            "blender equipment, and a blend instruction step."
        )
        if request.mode == "anchor" and anchors:
            liquid_anchors = [a for a in anchors if a.get("subcategory") == "liquid_base"]
            if liquid_anchors:
                names = ", ".join(a["name"] for a in liquid_anchors)
                prompt += (
                    f"\nANCHOR NOTE: Anchor(s) {names} are liquid_base ingredients — "
                    "assign them stage liquid_base in ml (typically 100-150ml). "
                    "You must still add blend-stage produce (g), not only the anchor."
                )
        transform_anchors = []
        for anchor in anchors or []:
            if constraints.beverage_type not in compute_eligible_beverage_types(anchor):
                opts = get_transforms_for_beverage_type(anchor, constraints.beverage_type)
                if opts:
                    transform_anchors.append(
                        f"{anchor['name']} (use stage={opts[0]['stage']}: {opts[0]['hint']})"
                    )
        if transform_anchors:
            prompt += (
                "\nANCHOR TRANSFORM REQUIRED: "
                + "; ".join(transform_anchors)
                + ". Set preparation on each anchor line to describe the transform."
            )
    elif constraints.beverage_type == "cold_press_juice":
        prompt += (
            "\n\nCONSTRAINT OVERRIDE: beverage_type is cold_press_juice. "
            "Apply COLD PRESS JUICE RULES — press-stage fresh produce; "
            "no liquid_base or prepared milks. "
            "Ingredients with transform_options may be used at finish stage only "
            "when preparation describes stirring powder/syrup in after pressing."
        )
    elif constraints.beverage_type in {"hot_tea", "infusion", "cold_brew"}:
        prompt += (
            f"\n\nCONSTRAINT OVERRIDE: beverage_type is {constraints.beverage_type}. "
            "Use steep-stage herbs/leaves only; water fills to 500ml."
        )
    elif constraints.beverage_type == "decoction":
        prompt += (
            "\n\nCONSTRAINT OVERRIDE: beverage_type is decoction. "
            "Simmer hard botanicals (roots, bark, seeds) and reduce to 500ml."
        )
    elif constraints.beverage_type == "fermented":
        prompt += (
            "\n\nCONSTRAINT OVERRIDE: beverage_type is fermented. "
            "Include a ferment-stage ingredient and fermentation step."
        )
    if constraints.beverage_type:
        prompt += (
            "\n\nTRANSFORMATION RULE: Pool entries may include transform_options when an "
            "ingredient is outside its default form for this beverage type. "
            "You MAY use them when they improve the formulation — but you MUST set "
            "stage and preparation on each ingredient line to match the transform hint. "
            "Prefer default-form ingredients when equally good."
        )
    return prompt


def _liquid_base_volume_ml(ingredient: dict[str, Any]) -> float:
    unit_metric = str(ingredient.get("unit_metric") or "").lower()
    if unit_metric == "ml":
        return float(ingredient.get("amount_metric") or 0)
    unit_imperial = str(ingredient.get("unit_imperial") or "").lower()
    if unit_imperial in {"fl_oz", "fl oz"}:
        return float(ingredient.get("amount_imperial") or 0) * 29.5735
    return 0.0


def _validate_smoothie(formulation: dict[str, Any]) -> None:
    if formulation.get("beverage_type") != "smoothie":
        return

    ingredients = formulation.get("ingredients") or []
    liquid_base = [i for i in ingredients if i.get("stage") == "liquid_base"]
    blend_items = [i for i in ingredients if i.get("stage") == "blend"]

    if not liquid_base:
        raise ValueError(
            "smoothie requires at least one liquid_base ingredient (water, nut milk, etc.) in ml"
        )

    liquid_ml = sum(_liquid_base_volume_ml(i) for i in liquid_base)
    if liquid_ml < 80:
        raise ValueError(
            f"smoothie liquid_base too low: {liquid_ml:.0f}ml (need ~100-150ml, minimum 80ml)"
        )

    if not blend_items:
        raise ValueError(
            "smoothie requires at least one blend-stage ingredient (produce, seeds, etc.)"
        )

    equipment = [str(e).lower() for e in (formulation.get("equipment_required") or [])]
    instruction_text = " ".join(
        str(s.get("action") or "") for s in (formulation.get("instructions") or [])
    ).lower()
    if not any("blender" in e for e in equipment) and "blend" not in instruction_text:
        raise ValueError("smoothie requires blender in equipment_required or a blend instruction step")


STAGES_BY_BEVERAGE_TYPE: dict[str, frozenset[str]] = {
    "cold_press_juice": frozenset({"press", "garnish", "finish"}),
    "smoothie": frozenset({"liquid_base", "blend", "garnish", "finish"}),
    "hot_tea": frozenset({"steep", "garnish", "finish"}),
    "infusion": frozenset({"steep", "garnish", "finish"}),
    "cold_brew": frozenset({"steep", "garnish", "finish"}),
    "decoction": frozenset({"steep", "finish", "garnish"}),
    "tonic": frozenset({"finish", "garnish", "steep", "blend", "liquid_base"}),
    "fermented": frozenset({"ferment", "finish", "garnish"}),
}


def _validate_beverage_type_formulation(
    formulation: dict[str, Any],
    ingredient_meta: dict[str, dict[str, Any]],
) -> None:
    beverage_type = formulation.get("beverage_type")
    if not beverage_type:
        return

    ingredients = formulation.get("ingredients") or []
    allowed_stages = STAGES_BY_BEVERAGE_TYPE.get(beverage_type, frozenset())

    for ing in ingredients:
        iid = str(ing["ingredient_id"])
        meta = ingredient_meta.get(iid)
        if not meta:
            continue

        usage_error = validate_ingredient_usage(meta, beverage_type, ing)
        if usage_error:
            raise ValueError(usage_error)

        stage = ing.get("stage") or ""
        if allowed_stages and stage not in allowed_stages:
            raise ValueError(f"stage '{stage}' is invalid for {beverage_type}")

    if beverage_type == "cold_press_juice":
        if not any(i.get("stage") == "press" for i in ingredients):
            raise ValueError("cold_press_juice requires at least one press-stage ingredient")
        if any(i.get("stage") in {"liquid_base", "blend", "steep", "ferment"} for i in ingredients):
            raise ValueError("cold_press_juice allows only press, garnish, and finish stages")

    elif beverage_type in {"hot_tea", "infusion", "cold_brew"}:
        if not any(i.get("stage") == "steep" for i in ingredients):
            raise ValueError(f"{beverage_type} requires at least one steep-stage ingredient")

    elif beverage_type == "decoction":
        if not any(i.get("stage") == "steep" for i in ingredients):
            raise ValueError("decoction requires at least one steep-stage (simmered) ingredient")

    elif beverage_type == "fermented":
        if not any(i.get("stage") == "ferment" for i in ingredients):
            raise ValueError("fermented requires at least one ferment-stage ingredient")

    _validate_smoothie(formulation)


def _validate_formulation(
    formulation: dict[str, Any],
    *,
    mode: str,
    anchor_ids: set[str],
    candidate_ids: set[str],
    max_ingredients: int,
    ingredient_meta: dict[str, dict[str, Any]],
) -> None:
    if formulation.get("yield_ml") != 500:
        raise ValueError("yield_ml must be 500")

    ingredients = formulation.get("ingredients") or []
    if not (3 <= len(ingredients) <= max_ingredients):
        raise ValueError(f"formulation must have 3-{max_ingredients} ingredients")

    instructions = formulation.get("instructions") or []
    if len(instructions) < 3:
        raise ValueError("formulation must have at least 3 instruction steps")

    selected_ids = {str(i["ingredient_id"]) for i in ingredients}
    if not selected_ids.issubset(candidate_ids):
        raise ValueError("formulation contains ingredient not in candidate pool")

    if mode == "anchor" and not anchor_ids.issubset(selected_ids):
        raise ValueError("anchor ingredient missing from formulation")

    for ing in ingredients:
        for field in ("amount_metric", "unit_metric", "amount_imperial", "unit_imperial", "stage"):
            if field not in ing or ing[field] is None:
                raise ValueError(f"ingredient missing required field: {field}")

    _validate_beverage_type_formulation(formulation, ingredient_meta)


def suggest_combinations(
    client: Client,
    request: CombinationSuggestRequest,
    anthropic: AnthropicService | None = None,
) -> CombinationSuggestResponse:
    constraints = request.constraints
    anchors: list[dict[str, Any]] = []

    if request.mode == "anchor":
        if not request.anchor_ingredient_ids:
            raise HTTPException(status_code=400, detail="anchor_ingredient_ids required for anchor mode")
        candidates = select_candidates_anchor(
            client,
            request.anchor_ingredient_ids,
            include_unverified=request.include_unverified,
            constraints=constraints,
        )
        for aid in request.anchor_ingredient_ids:
            row = fetch_ingredient(client, aid)
            if row:
                anchors.append(row)

        if constraints.beverage_type:
            anchor_conflicts = validate_anchors_for_beverage_type(anchors, constraints.beverage_type)
            if anchor_conflicts:
                primary = anchor_conflicts[0]
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": (
                            "Anchor ingredient(s) cannot be used with beverage type "
                            f"'{constraints.beverage_type}': "
                            + "; ".join(c["ingredient"] for c in anchor_conflicts)
                        ),
                        "suggestion": primary["suggestion"],
                        "anchor_conflicts": anchor_conflicts,
                        "candidate_pool_size": 0,
                    },
                )
    else:
        if not request.health_goals:
            raise HTTPException(status_code=400, detail="health_goals required for goal mode")
        candidates = select_candidates_goal(
            client,
            request.health_goals,
            include_unverified=request.include_unverified,
            constraints=constraints,
        )

    if len(candidates) < MIN_CANDIDATES:
        goals_hint = ", ".join(request.health_goals or [])
        raise HTTPException(
            status_code=422,
            detail={
                "error": f"Candidate pool too sparse for goal(s): {goals_hint}.",
                "suggestion": (
                    "Try broader goals (e.g. 'gut health' instead of 'high fiber'), "
                    "relax beverage type constraints, or enable include_unverified."
                ),
                "candidate_pool_size": len(candidates),
            },
        )

    service = anthropic or AnthropicService(model=get_combination_model_name())
    prompt = _build_prompt(request, candidates, anchors if request.mode == "anchor" else None)
    raw = service.complete_json(
        system="You are an expert beverage formulator. Output only valid JSON. Be concise.",
        user=prompt,
        max_tokens=4096,
    )

    if raw.get("error"):
        raise HTTPException(
            status_code=422,
            detail={
                "error": raw["error"],
                "suggestion": raw.get("suggestion"),
                "candidate_pool_size": len(candidates),
            },
        )

    candidate_ids = {str(c["id"]) for c in candidates}
    ingredient_meta = {str(c["id"]): c for c in candidates}
    for anchor in anchors:
        ingredient_meta[str(anchor["id"])] = anchor
    anchor_ids = {str(i) for i in (request.anchor_ingredient_ids or [])}
    formulations_raw = raw.get("formulations") or []

    validated: list[SuggestedFormulation] = []
    last_validation_error: str | None = None
    for item in formulations_raw[:3]:
        try:
            _validate_formulation(
                item,
                mode=request.mode,
                anchor_ids=anchor_ids,
                candidate_ids=candidate_ids,
                max_ingredients=constraints.max_ingredients,
                ingredient_meta=ingredient_meta,
            )
            # Flag unverified ingredients
            unverified_in_formulation = False
            for ing in item.get("ingredients") or []:
                meta = fetch_ingredient(client, UUID(str(ing["ingredient_id"])))
                if meta and meta.get("verification_status") == "unverified":
                    unverified_in_formulation = True
            item["contains_unverified_ingredients"] = (
                unverified_in_formulation or request.include_unverified
            )
            validated.append(SuggestedFormulation.model_validate(item))
        except Exception as exc:
            last_validation_error = str(exc)
            continue

    if not validated:
        suggestion = "Try relaxing constraints or adjusting health goals."
        if last_validation_error:
            suggestion = last_validation_error
        elif request.mode == "anchor" and constraints.beverage_type:
            suggestion = (
                "Ensure every anchor works with this beverage type. "
                "Prepared liquids (protein shakes, nut milks) are smoothie-only. "
                "For cold-press juice, anchor fresh produce to press."
            )
        raise HTTPException(
            status_code=422,
            detail={
                "error": "AI could not produce a valid recipe from the candidate pool.",
                "suggestion": suggestion,
                "candidate_pool_size": len(candidates),
            },
        )

    return CombinationSuggestResponse(
        formulations=validated,
        candidate_pool_size=len(candidates),
        exploratory_mode=request.include_unverified,
    )
