#!/usr/bin/env python3
"""
Create curated liquid-base ingredients and normalize smoothie beverage_types.

Usage:
  python scripts/setup_smoothie_pool.py
  python scripts/setup_smoothie_pool.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.beverage_type_eligibility import (  # noqa: E402
    compute_eligible_beverage_types,
    ineligibility_notes,
    normalize_beverage_types,
)

PENDING_DIR = BACKEND_ROOT / "pending_review"

# Curated pourable bases — subcategory liquid_base, optimized for health-forward smoothies.
LIQUID_BASES: list[dict] = [
    {
        "name": "Filtered water",
        "aliases": ["plain water", "still water", "spring water"],
        "category": "other",
        "flavour_intensity": 1,
        "beverage_types": ["smoothie", "cold_press_juice", "tonic"],
        "ratio_guidance": "100-150ml per 500ml smoothie as neutral liquid_base.",
        "preparation_notes": "Use filtered or spring water. Assign stage liquid_base in smoothie recipes.",
        "sourcing_notes": "Tap water filtered; bottled spring water acceptable.",
    },
    {
        "name": "Coconut water",
        "aliases": ["young coconut water"],
        "category": "other",
        "flavour_profile": ["sweet", "earthy"],
        "flavour_intensity": 2,
        "beverage_types": ["smoothie", "cold_press_juice", "tonic"],
        "body_systems": ["cardiovascular", "gut"],
        "active_compounds": ["potassium", "electrolytes"],
        "health_properties": {
            "traditional_claims": [],
            "evidence_based_claims": [
                {
                    "claim": "Natural source of potassium and electrolytes; used for hydration support",
                    "evidence_tier": "preliminary_research",
                    "source_type": "ai_generated",
                    "source_reference": None,
                    "confidence": "medium",
                }
            ],
        },
        "ratio_guidance": "100-150ml per 500ml smoothie; pairs well with tropical fruit.",
        "preparation_notes": "Use as liquid_base stage. Refrigerate after opening.",
        "sourcing_notes": "Carton or fresh young coconut; choose unsweetened when possible.",
    },
    {
        "name": "Almond milk (unsweetened)",
        "aliases": ["unsweetened almond milk"],
        "category": "other",
        "flavour_profile": ["nutty", "earthy"],
        "flavour_intensity": 2,
        "body_systems": ["gut"],
        "ratio_guidance": "100-150ml per 500ml smoothie as creamy liquid_base.",
        "preparation_notes": "Shake carton before use. Assign stage liquid_base.",
        "sourcing_notes": "Choose unsweetened, minimal additive brands for recipe consistency.",
    },
    {
        "name": "Oat milk (unsweetened)",
        "aliases": ["unsweetened oat milk"],
        "category": "other",
        "flavour_profile": ["sweet", "earthy"],
        "flavour_intensity": 2,
        "body_systems": ["gut", "cardiovascular"],
        "active_compounds": ["beta-glucan"],
        "health_properties": {
            "traditional_claims": [],
            "evidence_based_claims": [
                {
                    "claim": "Beta-glucan from oats may support cholesterol management at food-level intakes",
                    "evidence_tier": "established_research",
                    "source_type": "ai_generated",
                    "source_reference": None,
                    "confidence": "medium",
                }
            ],
        },
        "ratio_guidance": "100-150ml per 500ml smoothie; adds mild sweetness and body.",
        "preparation_notes": "Shake well. Works as liquid_base for green and berry smoothies.",
        "sourcing_notes": "Barista or standard unsweetened oat milk both work.",
    },
    {
        "name": "Coconut milk (light)",
        "aliases": ["lite coconut milk", "light coconut milk"],
        "category": "other",
        "flavour_profile": ["sweet", "earthy"],
        "flavour_intensity": 3,
        "body_systems": ["gut"],
        "active_compounds": ["medium-chain triglycerides"],
        "ratio_guidance": "80-120ml per 500ml smoothie; richer than coconut water.",
        "preparation_notes": "Use canned light coconut milk, shaken. liquid_base stage.",
        "sourcing_notes": "Light (not full-fat) coconut milk for drinkable consistency.",
    },
    {
        "name": "Cashew milk (unsweetened)",
        "aliases": ["unsweetened cashew milk"],
        "category": "other",
        "flavour_profile": ["nutty", "sweet"],
        "flavour_intensity": 2,
        "ratio_guidance": "100-150ml per 500ml smoothie; creamy neutral base.",
        "preparation_notes": "Shake before use. liquid_base stage in smoothies.",
        "sourcing_notes": "Unsweetened carton cashew milk.",
    },
    {
        "name": "Soy milk (unsweetened)",
        "aliases": ["unsweetened soy milk"],
        "category": "other",
        "flavour_profile": ["umami", "earthy"],
        "flavour_intensity": 2,
        "body_systems": ["gut", "musculoskeletal"],
        "active_compounds": ["complete plant protein", "isoflavones"],
        "health_properties": {
            "traditional_claims": [],
            "evidence_based_claims": [
                {
                    "claim": "Provides complete plant protein; soy isoflavones studied for cardiovascular and menopausal symptom support",
                    "evidence_tier": "established_research",
                    "source_type": "ai_generated",
                    "source_reference": None,
                    "confidence": "medium",
                }
            ],
        },
        "ratio_guidance": "100-150ml per 500ml smoothie as protein-rich liquid_base.",
        "preparation_notes": "Use plain unsweetened soy milk. liquid_base stage.",
        "sourcing_notes": "Plain unsweetened; avoid flavoured varieties in formulations.",
        "contraindications": ["Soy allergy"],
    },
    {
        "name": "Hemp milk (unsweetened)",
        "aliases": ["unsweetened hemp milk"],
        "category": "other",
        "flavour_profile": ["nutty", "earthy"],
        "flavour_intensity": 2,
        "body_systems": ["cardiovascular", "gut", "musculoskeletal"],
        "active_compounds": ["omega-3 ALA", "plant protein"],
        "health_properties": {
            "traditional_claims": [],
            "evidence_based_claims": [
                {
                    "claim": "Hemp seed provides ALA omega-3 and plant protein; milk is a convenient smoothie delivery format",
                    "evidence_tier": "preliminary_research",
                    "source_type": "ai_generated",
                    "source_reference": None,
                    "confidence": "medium",
                }
            ],
        },
        "ratio_guidance": "100-150ml per 500ml smoothie; nutty base with omega-3 support.",
        "preparation_notes": "Shake well. liquid_base stage.",
        "sourcing_notes": "Unsweetened hemp milk; check protein per serving on label.",
    },
    {
        "name": "Flax milk (unsweetened)",
        "aliases": ["unsweetened flax milk"],
        "category": "other",
        "flavour_profile": ["earthy", "nutty"],
        "flavour_intensity": 2,
        "body_systems": ["gut", "cardiovascular"],
        "active_compounds": ["alpha-linolenic acid", "lignans"],
        "health_properties": {
            "traditional_claims": [],
            "evidence_based_claims": [
                {
                    "claim": "Flax-derived ALA and lignans associated with cardiovascular and gut health in dietary studies",
                    "evidence_tier": "preliminary_research",
                    "source_type": "ai_generated",
                    "source_reference": None,
                    "confidence": "medium",
                }
            ],
        },
        "ratio_guidance": "100-150ml per 500ml smoothie; mild base with omega-3 support.",
        "preparation_notes": "Shake vigorously; liquid_base stage.",
        "sourcing_notes": "Unsweetened flax milk.",
    },
    {
        "name": "Plain kefir",
        "aliases": ["unsweetened kefir", "milk kefir"],
        "category": "fermented_base",
        "flavour_profile": ["sour", "earthy"],
        "flavour_intensity": 3,
        "body_systems": ["gut", "immune"],
        "active_compounds": ["probiotics", "protein", "calcium"],
        "health_properties": {
            "traditional_claims": [
                {
                    "claim": "Fermented milk drink traditionally used to support digestion",
                    "tradition": "Eastern European",
                    "source_type": "ai_generated",
                    "source_reference": None,
                    "confidence": "medium",
                }
            ],
            "evidence_based_claims": [
                {
                    "claim": "Fermented dairy with diverse probiotic cultures; studied for gut microbiome support",
                    "evidence_tier": "preliminary_research",
                    "source_type": "ai_generated",
                    "source_reference": None,
                    "confidence": "medium",
                }
            ],
        },
        "ratio_guidance": "100-150ml per 500ml smoothie; tangy probiotic liquid_base.",
        "preparation_notes": "Use plain unsweetened kefir as liquid_base. Blend immediately after combining.",
        "sourcing_notes": "Plain milk kefir; avoid heavily sweetened products.",
        "contraindications": ["Dairy allergy or lactose intolerance unless using dairy-free kefir"],
    },
    {
        "name": "Whey protein shake (plain, prepared)",
        "aliases": ["unflavored whey shake", "whey protein in water"],
        "category": "other",
        "flavour_profile": ["umami"],
        "flavour_intensity": 1,
        "body_systems": ["musculoskeletal", "immune"],
        "active_compounds": ["whey protein", "leucine", "immunoglobulins"],
        "health_properties": {
            "traditional_claims": [],
            "evidence_based_claims": [
                {
                    "claim": "Whey protein supports muscle protein synthesis and recovery when consumed around exercise",
                    "evidence_tier": "established_research",
                    "source_type": "ai_generated",
                    "source_reference": None,
                    "confidence": "high",
                }
            ],
        },
        "ratio_guidance": "100-150ml prepared shake per 500ml smoothie (typically 1 scoop whey in water).",
        "preparation_notes": "Prepare unflavored whey in water first; use as liquid_base stage.",
        "sourcing_notes": "Unflavored whey protein isolate or concentrate; mix with water before blending smoothie.",
        "contraindications": ["Dairy allergy or lactose intolerance"],
    },
    {
        "name": "Pea protein shake (plain, prepared)",
        "aliases": ["unflavored pea protein shake", "pea protein in water"],
        "category": "other",
        "flavour_profile": ["earthy"],
        "flavour_intensity": 2,
        "body_systems": ["musculoskeletal", "gut"],
        "active_compounds": ["pea protein", "iron"],
        "health_properties": {
            "traditional_claims": [],
            "evidence_based_claims": [
                {
                    "claim": "Pea protein supports muscle protein synthesis in plant-based diets; comparable to other plant proteins in short-term studies",
                    "evidence_tier": "preliminary_research",
                    "source_type": "ai_generated",
                    "source_reference": None,
                    "confidence": "medium",
                }
            ],
        },
        "ratio_guidance": "100-150ml prepared shake per 500ml smoothie.",
        "preparation_notes": "Dissolve unflavored pea protein in water; use as liquid_base stage.",
        "sourcing_notes": "Unflavored pea protein isolate.",
    },
    {
        "name": "Collagen peptide drink (unflavored, prepared)",
        "aliases": ["collagen water", "hydrolyzed collagen drink"],
        "category": "other",
        "flavour_profile": [],
        "flavour_intensity": 1,
        "body_systems": ["musculoskeletal", "skin"],
        "active_compounds": ["hydrolyzed collagen peptides", "glycine", "proline"],
        "health_properties": {
            "traditional_claims": [],
            "evidence_based_claims": [
                {
                    "claim": "Hydrolyzed collagen supplementation studied for skin elasticity and joint comfort in some trials",
                    "evidence_tier": "preliminary_research",
                    "source_type": "ai_generated",
                    "source_reference": None,
                    "confidence": "medium",
                }
            ],
        },
        "ratio_guidance": "100-150ml prepared drink per 500ml smoothie (typical 10-15g collagen in water).",
        "preparation_notes": "Dissolve unflavored collagen peptides in warm then cooled water; liquid_base stage.",
        "sourcing_notes": "Unflavored bovine or marine collagen peptides.",
    },
    {
        "name": "Bone broth (low-sodium)",
        "aliases": ["defatted bone broth", "chicken bone broth unsalted"],
        "category": "other",
        "flavour_profile": ["umami", "earthy"],
        "flavour_intensity": 3,
        "body_systems": ["gut", "musculoskeletal", "immune"],
        "active_compounds": ["collagen", "gelatin", "glycine", "minerals"],
        "health_properties": {
            "traditional_claims": [
                {
                    "claim": "Long-simmered broth traditionally used for convalescence and gut comfort",
                    "tradition": "Traditional European",
                    "source_type": "ai_generated",
                    "source_reference": None,
                    "confidence": "medium",
                }
            ],
            "evidence_based_claims": [
                {
                    "claim": "Gelatin and amino acids from bone broth may support gut lining integrity; clinical evidence remains limited",
                    "evidence_tier": "preliminary_research",
                    "source_type": "ai_generated",
                    "source_reference": None,
                    "confidence": "low",
                }
            ],
        },
        "ratio_guidance": "100-150ml per 500ml savory-leaning smoothie; pairs with greens and ginger.",
        "preparation_notes": "Use cooled low-sodium broth as liquid_base. Best in vegetable-forward blends.",
        "sourcing_notes": "Homemade or commercial low-sodium bone broth; refrigerate.",
    },
    {
        "name": "Tart cherry juice (unsweetened)",
        "aliases": ["montmorency cherry juice"],
        "category": "fruit",
        "flavour_profile": ["sour", "sweet"],
        "flavour_intensity": 3,
        "body_systems": ["musculoskeletal", "nervous_system"],
        "active_compounds": ["anthocyanins", "melatonin"],
        "health_properties": {
            "traditional_claims": [],
            "evidence_based_claims": [
                {
                    "claim": "Tart cherry juice studied for exercise recovery and sleep quality in small human trials",
                    "evidence_tier": "preliminary_research",
                    "source_type": "ai_generated",
                    "source_reference": None,
                    "confidence": "medium",
                }
            ],
        },
        "ratio_guidance": "80-120ml per 500ml smoothie; strong flavor — dilute with water if needed.",
        "preparation_notes": "Use as liquid_base; pairs with berry and recovery-focused blends.",
        "sourcing_notes": "100% tart cherry juice without added sugar.",
    },
    {
        "name": "Pomegranate juice (unsweetened)",
        "aliases": ["100% pomegranate juice"],
        "category": "fruit",
        "flavour_profile": ["sour", "astringent"],
        "flavour_intensity": 4,
        "body_systems": ["cardiovascular", "immune"],
        "active_compounds": ["punicalagins", "anthocyanins", "polyphenols"],
        "health_properties": {
            "traditional_claims": [],
            "evidence_based_claims": [
                {
                    "claim": "Pomegranate polyphenols associated with antioxidant activity and cardiovascular markers in human studies",
                    "evidence_tier": "preliminary_research",
                    "source_type": "ai_generated",
                    "source_reference": None,
                    "confidence": "medium",
                }
            ],
        },
        "ratio_guidance": "60-100ml per 500ml smoothie; potent — combine with mild bases.",
        "preparation_notes": "liquid_base stage; astringent — balance with sweet fruit.",
        "sourcing_notes": "100% pomegranate juice, no added sugar.",
        "contraindications": ["May interact with certain medications (e.g. statins, ACE inhibitors) at high intakes — consult clinician"],
    },
    {
        "name": "Beet juice",
        "aliases": ["beetroot juice"],
        "category": "vegetable",
        "flavour_profile": ["earthy", "sweet"],
        "flavour_intensity": 3,
        "body_systems": ["cardiovascular", "musculoskeletal"],
        "active_compounds": ["dietary nitrates", "betaine"],
        "health_properties": {
            "traditional_claims": [],
            "evidence_based_claims": [
                {
                    "claim": "Dietary nitrates from beetroot may improve exercise performance and blood pressure in some studies",
                    "evidence_tier": "established_research",
                    "source_type": "ai_generated",
                    "source_reference": None,
                    "confidence": "medium",
                }
            ],
        },
        "ratio_guidance": "60-100ml per 500ml smoothie; earthy base for cardiovascular-focused blends.",
        "preparation_notes": "Use as liquid_base; stains equipment — rinse blender promptly.",
        "sourcing_notes": "Fresh-pressed or bottled 100% beet juice.",
        "contraindications": ["High oxalate content — caution with kidney stone history"],
    },
    {
        "name": "Aloe vera juice (inner leaf)",
        "aliases": ["aloe inner leaf juice", "decolorized aloe juice"],
        "category": "other",
        "flavour_profile": ["bitter", "earthy"],
        "flavour_intensity": 2,
        "body_systems": ["gut", "skin"],
        "active_compounds": ["polysaccharides", "acemannan"],
        "health_properties": {
            "traditional_claims": [
                {
                    "claim": "Inner leaf aloe traditionally used for digestive comfort",
                    "tradition": "Ayurvedic",
                    "source_type": "ai_generated",
                    "source_reference": None,
                    "confidence": "medium",
                }
            ],
            "evidence_based_claims": [
                {
                    "claim": "Inner leaf aloe juice studied for occasional constipation relief; laxative anthraquinones should be removed in food-grade products",
                    "evidence_tier": "preliminary_research",
                    "source_type": "ai_generated",
                    "source_reference": None,
                    "confidence": "medium",
                }
            ],
        },
        "ratio_guidance": "60-100ml per 500ml smoothie; use food-grade decolorized inner leaf juice only.",
        "preparation_notes": "liquid_base stage. Use products labeled for internal consumption.",
        "sourcing_notes": "Decolorized inner fillet aloe juice; avoid whole-leaf laxative products.",
        "contraindications": ["Not recommended in pregnancy; may interact with diabetes and diuretic medications"],
    },
    {
        "name": "Green tea (brewed, cooled)",
        "aliases": ["cooled green tea", "brewed sencha base"],
        "category": "herb",
        "flavour_profile": ["earthy", "astringent"],
        "flavour_intensity": 2,
        "body_systems": ["immune", "cardiovascular", "nervous_system"],
        "active_compounds": ["EGCG", "L-theanine", "caffeine"],
        "health_properties": {
            "traditional_claims": [
                {
                    "claim": "Green tea traditionally consumed for alert calm and general vitality",
                    "tradition": "TCM",
                    "source_type": "ai_generated",
                    "source_reference": None,
                    "confidence": "high",
                }
            ],
            "evidence_based_claims": [
                {
                    "claim": "Catechins and L-theanine in green tea associated with antioxidant and cognitive support in research",
                    "evidence_tier": "established_research",
                    "source_type": "ai_generated",
                    "source_reference": None,
                    "confidence": "medium",
                }
            ],
        },
        "ratio_guidance": "100-150ml brewed cooled tea per 500ml smoothie as antioxidant liquid_base.",
        "preparation_notes": "Brew 2-3g leaf in 150ml water, cool before blending. liquid_base stage.",
        "sourcing_notes": "Loose leaf or bagged green tea; brew fresh.",
        "contraindications": ["Caffeine sensitivity", "Iron absorption may be reduced when taken with meals"],
    },
    {
        "name": "Matcha (prepared)",
        "aliases": ["prepared matcha beverage", "whisked matcha base"],
        "category": "herb",
        "flavour_profile": ["earthy", "umami"],
        "flavour_intensity": 3,
        "body_systems": ["immune", "nervous_system", "cardiovascular"],
        "active_compounds": ["EGCG", "L-theanine", "caffeine", "chlorophyll"],
        "health_properties": {
            "traditional_claims": [
                {
                    "claim": "Matcha used in Japanese tea ceremony for focused alertness",
                    "tradition": "Japanese",
                    "source_type": "ai_generated",
                    "source_reference": None,
                    "confidence": "high",
                }
            ],
            "evidence_based_claims": [
                {
                    "claim": "Whole-leaf matcha provides higher catechin intake than steeped green tea; L-theanine may modulate caffeine effects",
                    "evidence_tier": "preliminary_research",
                    "source_type": "ai_generated",
                    "source_reference": None,
                    "confidence": "medium",
                }
            ],
        },
        "ratio_guidance": "100-120ml prepared matcha (1-2g powder whisked in water) per 500ml smoothie.",
        "preparation_notes": "Whisk matcha into warm water, cool, then use as liquid_base.",
        "sourcing_notes": "Ceremonial or culinary grade matcha; sift before whisking.",
        "contraindications": ["Caffeine sensitivity"],
    },
]


def slugify(name: str) -> str:
    import re

    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "ingredient"


def base_payload(spec: dict) -> dict:
    payload = {
        "name": spec["name"],
        "aliases": spec.get("aliases", []),
        "category": spec["category"],
        "subcategory": "liquid_base",
        "origin": spec.get("origin", []),
        "traditions": spec.get("traditions", []),
        "flavour_profile": spec.get("flavour_profile", []),
        "flavour_intensity": spec.get("flavour_intensity"),
        "primary_terpene": spec.get("primary_terpene"),
        "secondary_terpenes": spec.get("secondary_terpenes", []),
        "beverage_types": spec.get("beverage_types", ["smoothie"]),
        "health_properties": spec.get(
            "health_properties",
            {"traditional_claims": [], "evidence_based_claims": []},
        ),
        "body_systems": spec.get("body_systems", []),
        "active_compounds": spec.get("active_compounds", []),
        "bioavailability_notes": spec.get("bioavailability_notes"),
        "preparation_notes": spec.get("preparation_notes"),
        "contraindications": spec.get("contraindications", []),
        "combination_contraindications": spec.get("combination_contraindications", []),
        "ratio_guidance": spec.get("ratio_guidance"),
        "rarity_score": spec.get("rarity_score", "common"),
        "sourcing_notes": spec.get("sourcing_notes"),
        "history": spec.get("history"),
        "personal_notes": spec.get("personal_notes"),
        "entry_source_type": "ai_generated",
        "entry_confidence": spec.get("entry_confidence", "high"),
        "verification_status": "unverified",
        "verification_notes": spec.get("verification_notes"),
        "last_verified_at": None,
    }
    return normalize_beverage_types(payload, slug=slugify(spec["name"]))


def write_liquid_bases(dry_run: bool) -> list[str]:
    created: list[str] = []
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    for spec in LIQUID_BASES:
        path = PENDING_DIR / f"{slugify(spec['name'])}.json"
        payload = base_payload(spec)
        if dry_run:
            print(f"  [dry-run] Would write liquid base: {spec['name']}")
        else:
            path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"  Wrote liquid base: {spec['name']}")
        created.append(spec["name"])
    return created


def normalize_all_smoothie_tags(dry_run: bool) -> tuple[list[str], list[str]]:
    """Apply eligibility rules to every non-liquid-base pending ingredient."""
    updated: list[str] = []
    excluded: list[str] = []
    for path in sorted(PENDING_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("subcategory") == "liquid_base":
            continue
        before = list(data.get("beverage_types") or [])
        normalized = normalize_beverage_types(data, slug=path.stem)
        after = list(normalized.get("beverage_types") or [])
        reason = ineligibility_notes(normalized, "smoothie", slug=path.stem)
        if reason:
            excluded.append(f"{normalized['name']}: {reason}")
        if before != after:
            if dry_run:
                print(f"  [dry-run] {normalized['name']}: {before} -> {after}")
            else:
                path.write_text(json.dumps(normalized, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                print(f"  Normalized: {normalized['name']}  {before} -> {after}")
            updated.append(normalized["name"])
    return updated, excluded


def main() -> None:
    parser = argparse.ArgumentParser(description="Set up smoothie liquid bases and normalize beverage_types")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("Writing liquid-base ingredients…")
    bases = write_liquid_bases(args.dry_run)
    print("\nNormalizing smoothie tags by eligibility rules…")
    updated, excluded = normalize_all_smoothie_tags(args.dry_run)

    print("\n" + "=" * 50)
    print("SMOOTHIE POOL SETUP")
    print("=" * 50)
    print(f"  Liquid bases:         {len(bases)}")
    print(f"  Tags normalized:      {len(updated)}")
    print(f"  Smoothie-ineligible:  {len(excluded)}")
    for line in excluded:
        print(f"    - {line}")
    if not args.dry_run:
        print("\nNext: python scripts/sync_pending_ingredients.py")
    print("=" * 50)


if __name__ == "__main__":
    main()
