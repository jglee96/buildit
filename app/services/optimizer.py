from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from math import ceil, cos, floor, pi, sin, sqrt
from time import perf_counter
from typing import Optional

from app.models import ProjectAestheticInput, ProjectRequirement, RuleDefinition
from app.schemas import ConstraintCheck
from app.services.rule_dsl import evaluate_expression


@dataclass
class Candidate:
    far: float
    height: float
    coverage: float
    open_space_ratio: float
    sky_exposure: float
    articulation_index: float
    option_type: str
    block_count: int
    floorplate_area_m2: float
    floors: int
    building_spacing_m: float
    max_block_length_m: float
    plan_family: str
    unit_mix: dict[str, float]
    avg_unit_area_m2: float
    footprint_width_m: float
    footprint_depth_m: float


def _requirement_map(requirements: list[ProjectRequirement]) -> dict[str, ProjectRequirement]:
    return {item.key: item for item in requirements}


def _extract_limit(rule_definitions: list[RuleDefinition], key: str) -> Optional[float]:
    for definition in rule_definitions:
        if definition.rule_key != key:
            continue
        if definition.expression.get("op") in {"lte", "eq"}:
            return float(definition.expression.get("value"))
    return None


def _site_metrics(site_geojson: dict) -> dict:
    coordinates = site_geojson.get("coordinates", [])
    if not coordinates or not coordinates[0] or len(coordinates[0]) < 4:
        ring_m = [(-25.0, -25.0), (25.0, -25.0), (25.0, 25.0), (-25.0, 25.0), (-25.0, -25.0)]
        return {
            "area_m2": 2500.0,
            "width_m": 50.0,
            "depth_m": 50.0,
            "ring_m": ring_m,
        }

    ring_ll = coordinates[0]
    lng_center = sum(point[0] for point in ring_ll) / len(ring_ll)
    lat_center = sum(point[1] for point in ring_ll) / len(ring_ll)

    ring_m: list[tuple[float, float]] = []
    for lng, lat in ring_ll:
        x = (lng - lng_center) * 111320.0 * cos((lat_center * pi) / 180.0)
        z = (lat - lat_center) * 110540.0
        ring_m.append((x, z))

    if ring_m[0] != ring_m[-1]:
        ring_m.append(ring_m[0])

    twice_area = 0.0
    min_x = min(point[0] for point in ring_m)
    max_x = max(point[0] for point in ring_m)
    min_z = min(point[1] for point in ring_m)
    max_z = max(point[1] for point in ring_m)

    for idx in range(len(ring_m) - 1):
        x1, z1 = ring_m[idx]
        x2, z2 = ring_m[idx + 1]
        twice_area += x1 * z2 - x2 * z1

    area = max(500.0, abs(twice_area) / 2.0)
    width = max(24.0, max_x - min_x)
    depth = max(24.0, max_z - min_z)
    return {
        "area_m2": area,
        "width_m": width,
        "depth_m": depth,
        "ring_m": ring_m,
    }


def _point_in_polygon(x: float, z: float, ring: list[tuple[float, float]]) -> bool:
    inside = False
    for idx in range(len(ring) - 1):
        x1, z1 = ring[idx]
        x2, z2 = ring[idx + 1]
        intersects = ((z1 > z) != (z2 > z)) and (x < (x2 - x1) * (z - z1) / ((z2 - z1) or 1e-9) + x1)
        if intersects:
            inside = not inside
    return inside


def _block_inside_polygon(
    *,
    x: float,
    z: float,
    width: float,
    depth: float,
    ring: list[tuple[float, float]],
    safety_offset: float = 0.6,
) -> bool:
    half_w = (width / 2.0) + safety_offset
    half_d = (depth / 2.0) + safety_offset
    corners = [
        (x - half_w, z - half_d),
        (x + half_w, z - half_d),
        (x + half_w, z + half_d),
        (x - half_w, z + half_d),
    ]
    return all(_point_in_polygon(cx, cz, ring) for cx, cz in corners)


def _country_defaults(country_code: str) -> dict[str, float]:
    normalized = (country_code or "KR").upper()
    if normalized == "SG":
        return {
            "coverage_upper": 50.0,
            "open_space_min": 28.0,
            "sky_exposure_max": 0.72,
            "height_soft_upper": 140.0,
            "min_building_spacing": 24.0,
        }
    if normalized in {"US", "US-NYC", "NYC"}:
        return {
            "coverage_upper": 68.0,
            "open_space_min": 20.0,
            "sky_exposure_max": 0.78,
            "height_soft_upper": 180.0,
            "min_building_spacing": 20.0,
        }
    return {
        "coverage_upper": 60.0,
        "open_space_min": 22.0,
        "sky_exposure_max": 0.68,
        "height_soft_upper": 120.0,
        "min_building_spacing": 24.0,
    }


def _residential_unit_model(country_code: str) -> tuple[dict[str, float], float]:
    normalized = (country_code or "KR").upper()
    if normalized == "SG":
        mix = {"65": 0.26, "85": 0.48, "110": 0.26}
    elif normalized in {"US", "US-NYC", "NYC"}:
        mix = {"70": 0.25, "90": 0.45, "120": 0.3}
    else:
        mix = {"59": 0.36, "74": 0.2, "84": 0.34, "101": 0.1}

    average = 0.0
    for key, weight in mix.items():
        average += float(key) * weight
    return mix, round(average, 2)


def _residential_candidates(
    *,
    far_upper: float,
    height_upper: float,
    coverage_upper: float,
    open_space_min: float,
    site_metrics: dict,
    min_spacing: float,
    country_code: str,
) -> list[Candidate]:
    site_area_m2 = site_metrics["area_m2"]
    site_width_m = site_metrics["width_m"]
    site_depth_m = site_metrics["depth_m"]

    unit_mix, avg_unit_area = _residential_unit_model(country_code)
    floor_to_floor = 3.1

    variants = [
        {
            "option_type": "apartment_linear_cluster",
            "plan_family": "plate",
            "far_factor": 1.0,
            "height_factor": 0.82,
            "base_floorplate": 760.0,
            "slenderness": 2.25,
            "articulation": 81.0,
        },
        {
            "option_type": "apartment_tower_cluster",
            "plan_family": "tower",
            "far_factor": 0.95,
            "height_factor": 0.9,
            "base_floorplate": 560.0,
            "slenderness": 1.35,
            "articulation": 88.0,
        },
        {
            "option_type": "apartment_hybrid_cluster",
            "plan_family": "hybrid",
            "far_factor": 0.92,
            "height_factor": 0.78,
            "base_floorplate": 640.0,
            "slenderness": 1.75,
            "articulation": 90.0,
        },
    ]

    candidates: list[Candidate] = []
    for variant in variants:
        target_far = far_upper * variant["far_factor"]
        height = height_upper * variant["height_factor"]
        floors = max(8, min(35, int(height / floor_to_floor)))

        gfa_target = site_area_m2 * (target_far / 100.0)
        base_floorplate = variant["base_floorplate"]
        initial_blocks = max(2, int(ceil(gfa_target / max(1.0, base_floorplate * floors))))
        block_count = min(8, initial_blocks)

        spacing = max(min_spacing, height * 0.55 if country_code.upper() == "KR" else height * 0.45)

        base_width = sqrt(max(base_floorplate, 300.0)) * variant["slenderness"]
        base_depth = max(11.0, base_floorplate / max(base_width, 1.0))

        footprint_width = min(base_width, site_width_m * 0.42)
        footprint_depth = min(base_depth, site_depth_m * 0.42)

        cols_capacity = max(1, int(floor((site_width_m + spacing) / max(1.0, (footprint_width + spacing)))))
        rows_capacity = max(1, int(floor((site_depth_m + spacing) / max(1.0, (footprint_depth + spacing)))))
        layout_capacity = max(1, cols_capacity * rows_capacity)
        block_count = min(block_count, layout_capacity)

        max_floorplate_by_coverage = (site_area_m2 * (coverage_upper / 100.0)) / max(block_count, 1)
        floorplate = min(base_floorplate, max_floorplate_by_coverage, footprint_width * footprint_depth)
        footprint_depth = max(10.0, floorplate / max(footprint_width, 1.0))

        achieved_gfa = floorplate * floors * block_count
        achieved_far = min(target_far, (achieved_gfa / site_area_m2) * 100.0)
        coverage = (floorplate * block_count / site_area_m2) * 100.0
        open_space = max(open_space_min, 100.0 - coverage)

        max_block_length = max(footprint_width, footprint_depth)
        sky_exposure = min(0.9, height / max(20.0, spacing * 2.95))

        candidates.append(
            Candidate(
                far=achieved_far,
                height=height,
                coverage=coverage,
                open_space_ratio=open_space,
                sky_exposure=sky_exposure,
                articulation_index=variant["articulation"],
                option_type=variant["option_type"],
                block_count=max(1, block_count),
                floorplate_area_m2=floorplate,
                floors=floors,
                building_spacing_m=spacing,
                max_block_length_m=max_block_length,
                plan_family=variant["plan_family"],
                unit_mix=unit_mix,
                avg_unit_area_m2=avg_unit_area,
                footprint_width_m=footprint_width,
                footprint_depth_m=footprint_depth,
            )
        )

    return candidates


def _non_residential_candidates(
    *,
    far_upper: float,
    height_upper: float,
    coverage_upper: float,
    open_space_min: float,
) -> list[Candidate]:
    return [
        Candidate(
            far=far_upper,
            height=height_upper * 0.88,
            coverage=min(coverage_upper, 48.0),
            open_space_ratio=max(open_space_min, 52.0),
            sky_exposure=0.62,
            articulation_index=82.0,
            option_type="podium_tower",
            block_count=1,
            floorplate_area_m2=720.0,
            floors=max(5, int((height_upper * 0.88) / 3.6)),
            building_spacing_m=0.0,
            max_block_length_m=58.0,
            plan_family="single_mass",
            unit_mix={"-": 1.0},
            avg_unit_area_m2=0.0,
            footprint_width_m=44.0,
            footprint_depth_m=30.0,
        ),
        Candidate(
            far=far_upper * 0.94,
            height=height_upper * 0.8,
            coverage=min(coverage_upper, 42.0),
            open_space_ratio=max(open_space_min + 3.0, 58.0),
            sky_exposure=0.58,
            articulation_index=90.0,
            option_type="stepped_slab",
            block_count=1,
            floorplate_area_m2=660.0,
            floors=max(5, int((height_upper * 0.8) / 3.6)),
            building_spacing_m=0.0,
            max_block_length_m=52.0,
            plan_family="single_mass",
            unit_mix={"-": 1.0},
            avg_unit_area_m2=0.0,
            footprint_width_m=40.0,
            footprint_depth_m=28.0,
        ),
        Candidate(
            far=far_upper * 0.9,
            height=height_upper * 0.74,
            coverage=min(coverage_upper, 52.0),
            open_space_ratio=max(open_space_min + 6.0, 56.0),
            sky_exposure=0.56,
            articulation_index=86.0,
            option_type="courtyard_block",
            block_count=1,
            floorplate_area_m2=820.0,
            floors=max(5, int((height_upper * 0.74) / 3.6)),
            building_spacing_m=0.0,
            max_block_length_m=60.0,
            plan_family="single_mass",
            unit_mix={"-": 1.0},
            avg_unit_area_m2=0.0,
            footprint_width_m=50.0,
            footprint_depth_m=34.0,
        ),
    ]


def _market_fit_score(candidate: Candidate, occupancy_type: str) -> float:
    if occupancy_type not in {"residential", "mixed_use"}:
        return 72.0
    size_fit = max(40.0, 100.0 - abs(candidate.avg_unit_area_m2 - 80.0) * 1.6)
    plan_fit_bonus = 8.0 if candidate.plan_family in {"plate", "tower", "hybrid"} else 0.0
    dong_fit = min(18.0, candidate.block_count * 2.5)
    return min(100.0, size_fit + plan_fit_bonus + dong_fit)


def _qualitative_score(candidate: Candidate, aesthetic_inputs: list[ProjectAestheticInput], occupancy_type: str) -> dict[str, float]:
    all_text = " ".join(item.content.lower() for item in aesthetic_inputs)
    has_landmark_bias = any(token in all_text for token in ["랜드마크", "iconic", "상징"])
    has_context_bias = any(token in all_text for token in ["맥락", "조화", "context", "street"])

    reference_count = sum(1 for item in aesthetic_inputs if item.reference_url)
    mean_weight = sum(item.weight for item in aesthetic_inputs) / max(len(aesthetic_inputs), 1)

    skyline_harmony = 76.0
    if "tower" in candidate.option_type:
        skyline_harmony = 86.0
    elif "courtyard" in candidate.option_type:
        skyline_harmony = 84.0
    elif "linear" in candidate.option_type:
        skyline_harmony = 82.0

    if not has_landmark_bias and candidate.height > 85.0:
        skyline_harmony -= 8.0
    if has_context_bias:
        skyline_harmony += 4.0

    street_scale_fit = max(40.0, 100.0 - abs(candidate.coverage - 45.0) * 1.4)
    open_space_quality = max(40.0, min(100.0, candidate.open_space_ratio * 1.7 + 15.0))
    reference_maturity = max(45.0, min(100.0, 46.0 + (reference_count * 9.0) + (len(aesthetic_inputs) * 2.0)))
    market_fit = _market_fit_score(candidate, occupancy_type)

    total = (
        skyline_harmony * 0.3
        + street_scale_fit * 0.24
        + open_space_quality * 0.22
        + market_fit * 0.16
        + reference_maturity * 0.08
    )
    total = min(100.0, max(0.0, total * (0.9 + (mean_weight * 0.1))))

    return {
        "skyline_harmony": round(skyline_harmony, 2),
        "street_scale_fit": round(street_scale_fit, 2),
        "open_space_quality": round(open_space_quality, 2),
        "reference_maturity": round(reference_maturity, 2),
        "market_fit": round(market_fit, 2),
        "total": round(total, 2),
    }


def _score_candidate(candidate: Candidate, qualitative_total: float) -> float:
    far_component = candidate.far * 0.6
    qualitative_component = qualitative_total * 1.0
    massing_penalty = max(0.0, candidate.coverage - 58.0) * 2.0
    long_block_penalty = max(0.0, candidate.max_block_length_m - 70.0) * 0.9
    return far_component + qualitative_component - massing_penalty - long_block_penalty


def _legal_basis(country_code: str, occupancy_type: str) -> list[str]:
    normalized = (country_code or "KR").upper()
    if normalized == "SG":
        base = [
            "URA Development Control (Gross Plot Ratio)",
            "URA Urban Design Guidelines (setback/street wall)",
        ]
    elif normalized in {"US", "US-NYC", "NYC"}:
        base = [
            "NYC Zoning Resolution (FAR)",
            "NYC Zoning controls for form and sky exposure",
        ]
    else:
        base = [
            "국토계획법 시행령 제85조(용적률)",
            "건축법 제61조 및 관련 조례(일조/높이/이격)",
            "주택법 제2조(국민주택규모 85㎡ 기준)",
            "지자체 경관/건축위원회 심의기준",
        ]

    if occupancy_type in {"residential", "mixed_use"}:
        base.append("주택건설기준 등에 관한 규정(공동주택 배치/채광 관련)")
    return base


def _layout_blocks_within_polygon(
    *,
    block_count: int,
    width: float,
    depth: float,
    spacing: float,
    ring: list[tuple[float, float]],
) -> list[dict]:
    # Try several shrink ratios to guarantee blocks stay inside polygon.
    for ratio in [1.0, 0.93, 0.87, 0.82, 0.76, 0.7, 0.62, 0.54, 0.46]:
        local_width = width * ratio
        local_depth = depth * ratio
        local_spacing = spacing * ratio

        cols = int(ceil(sqrt(block_count)))
        rows = int(ceil(block_count / cols))
        span_x = (cols - 1) * (local_width + local_spacing)
        span_z = (rows - 1) * (local_depth + local_spacing)

        blocks: list[dict] = []
        for idx in range(block_count):
            row = idx // cols
            col = idx % cols
            x = (col - (cols - 1) / 2.0) * (local_width + local_spacing)
            z = (row - (rows - 1) / 2.0) * (local_depth + local_spacing)

            if _block_inside_polygon(x=x, z=z, width=local_width, depth=local_depth, ring=ring):
                blocks.append({"x": x, "z": z, "width": local_width, "depth": local_depth})

        if len(blocks) >= block_count:
            return blocks[:block_count]

        # If full fit fails, accept a reduced count but still keep minimum livable cluster.
        if len(blocks) >= 2:
            return blocks

    return []


def _build_mesh(candidate: Candidate, site_metrics: dict, occupancy_type: str) -> dict:
    site_area_m2 = site_metrics["area_m2"]
    ring = site_metrics["ring_m"]

    if occupancy_type in {"residential", "mixed_use"} and candidate.block_count > 1:
        laid_out = _layout_blocks_within_polygon(
            block_count=candidate.block_count,
            width=candidate.footprint_width_m,
            depth=candidate.footprint_depth_m,
            spacing=candidate.building_spacing_m,
            ring=ring,
        )

        blocks = []
        for idx, block in enumerate(laid_out):
            height_scale = 1.0 - (0.06 * (idx % 2))
            blocks.append(
                {
                    "x": round(block["x"], 2),
                    "z": round(block["z"], 2),
                    "width": round(block["width"], 2),
                    "depth": round(block["depth"], 2),
                    "height": round(candidate.height * height_scale, 2),
                }
            )

        return {
            "type": "multi_block",
            "blocks": blocks,
            "site_outline": [[round(x, 2), round(z, 2)] for x, z in ring],
            "origin": [0, 0, 0],
        }

    footprint_area = site_area_m2 * (candidate.coverage / 100.0)
    base_width = max(18.0, min(65.0, (footprint_area ** 0.5) * 1.08))
    base_depth = max(16.0, min(60.0, (footprint_area ** 0.5) * 0.92))

    if candidate.option_type == "podium_tower":
        podium_height = min(18.0, candidate.height * 0.28)
        tower_height = max(12.0, candidate.height - podium_height)
        return {
            "type": "stacked",
            "segments": [
                {"width": round(base_width, 2), "depth": round(base_depth, 2), "height": round(podium_height, 2), "base_y": 0.0},
                {
                    "width": round(base_width * 0.62, 2),
                    "depth": round(base_depth * 0.62, 2),
                    "height": round(tower_height, 2),
                    "base_y": round(podium_height, 2),
                },
            ],
            "origin": [0, 0, 0],
        }

    if candidate.option_type == "stepped_slab":
        level1 = candidate.height * 0.42
        level2 = candidate.height * 0.32
        level3 = candidate.height - level1 - level2
        return {
            "type": "stacked",
            "segments": [
                {"width": round(base_width, 2), "depth": round(base_depth, 2), "height": round(level1, 2), "base_y": 0.0},
                {
                    "width": round(base_width * 0.82, 2),
                    "depth": round(base_depth * 0.82, 2),
                    "height": round(level2, 2),
                    "base_y": round(level1, 2),
                },
                {
                    "width": round(base_width * 0.66, 2),
                    "depth": round(base_depth * 0.66, 2),
                    "height": round(level3, 2),
                    "base_y": round(level1 + level2, 2),
                },
            ],
            "origin": [0, 0, 0],
        }

    return {
        "type": "courtyard",
        "outer_width": round(base_width, 2),
        "outer_depth": round(base_depth, 2),
        "inner_width": round(base_width * 0.42, 2),
        "inner_depth": round(base_depth * 0.42, 2),
        "height": round(candidate.height, 2),
        "origin": [0, 0, 0],
    }


def optimize_options(
    *,
    rule_definitions: list[RuleDefinition],
    requirements: list[ProjectRequirement],
    objective: str,
    site_geojson: dict,
    country_code: str,
    occupancy_type: str,
    aesthetic_inputs: list[ProjectAestheticInput],
) -> tuple[list[dict], dict[str, float]]:
    t_total = perf_counter()
    t_phase = perf_counter()
    req_map = _requirement_map(requirements)
    user_far_min = req_map.get("far").min_value if req_map.get("far") else None
    user_far_max = req_map.get("far").max_value if req_map.get("far") else None
    user_height_max = req_map.get("height").max_value if req_map.get("height") else None
    user_qualitative_min = req_map.get("qualitative_min").min_value if req_map.get("qualitative_min") else None

    defaults = _country_defaults(country_code)
    rule_far_max = _extract_limit(rule_definitions, "max_far")
    rule_height_max = _extract_limit(rule_definitions, "max_height")
    rule_coverage_max = _extract_limit(rule_definitions, "max_coverage")
    rule_sky_exposure_max = _extract_limit(rule_definitions, "max_sky_exposure")
    rule_open_space_min = _extract_limit(rule_definitions, "min_open_space")

    far_upper = min(x for x in [user_far_max, rule_far_max, 999.0] if x is not None)
    height_upper = min(x for x in [user_height_max, rule_height_max, defaults["height_soft_upper"]] if x is not None)
    coverage_upper = min(x for x in [rule_coverage_max, defaults["coverage_upper"]] if x is not None)
    sky_exposure_max = min(x for x in [rule_sky_exposure_max, defaults["sky_exposure_max"]] if x is not None)
    open_space_min = max(x for x in [rule_open_space_min, defaults["open_space_min"]] if x is not None)

    site_metrics = _site_metrics(site_geojson)
    timings: dict[str, float] = {
        "prepare_inputs_ms": round((perf_counter() - t_phase) * 1000.0, 3),
    }

    t_phase = perf_counter()
    if occupancy_type in {"residential", "mixed_use"}:
        raw_candidates = _residential_candidates(
            far_upper=far_upper,
            height_upper=height_upper,
            coverage_upper=coverage_upper,
            open_space_min=open_space_min,
            site_metrics=site_metrics,
            min_spacing=defaults["min_building_spacing"],
            country_code=country_code,
        )
    else:
        raw_candidates = _non_residential_candidates(
            far_upper=far_upper,
            height_upper=height_upper,
            coverage_upper=coverage_upper,
            open_space_min=open_space_min,
        )
    timings["candidate_generation_ms"] = round((perf_counter() - t_phase) * 1000.0, 3)

    options: list[dict] = []
    mesh_ms = 0.0
    qualitative_ms = 0.0
    checks_ms = 0.0
    for candidate in raw_candidates:
        t_step = perf_counter()
        mesh_payload = _build_mesh(candidate, site_metrics, occupancy_type)
        mesh_ms += perf_counter() - t_step

        actual_block_count = candidate.block_count
        if mesh_payload.get("type") == "multi_block":
            actual_block_count = len(mesh_payload.get("blocks", []))

        block_ratio = actual_block_count / max(candidate.block_count, 1)
        effective_far = candidate.far * block_ratio
        effective_coverage = candidate.coverage * block_ratio
        effective_open_space = max(open_space_min, 100.0 - effective_coverage)

        candidate_for_quality = Candidate(
            **{**candidate.__dict__, "far": effective_far, "coverage": effective_coverage, "open_space_ratio": effective_open_space, "block_count": actual_block_count}
        )
        t_step = perf_counter()
        qualitative = _qualitative_score(candidate_for_quality, aesthetic_inputs, occupancy_type)
        qualitative_ms += perf_counter() - t_step

        t_step = perf_counter()
        state = {
            "far": effective_far,
            "height": candidate.height,
            "coverage": effective_coverage,
            "open_space": effective_open_space,
            "sky_exposure": candidate.sky_exposure,
            "articulation_index": candidate.articulation_index,
            "block_count": actual_block_count,
            "max_block_length": candidate.max_block_length_m,
            "min_block_spacing": candidate.building_spacing_m,
        }

        checks: list[ConstraintCheck] = []
        feasible = True
        for definition in rule_definitions:
            passed, detail = evaluate_expression(definition.expression, state)
            checks.append(
                ConstraintCheck(
                    rule_key=definition.rule_key,
                    rule_type=definition.rule_type,
                    passed=passed,
                    detail=detail,
                )
            )
            if definition.rule_type == "hard" and not passed:
                feasible = False

        if candidate.sky_exposure > sky_exposure_max:
            feasible = False
            checks.append(
                ConstraintCheck(
                    rule_key="sky_exposure_cap",
                    rule_type="hard",
                    passed=False,
                    detail=f"sky_exposure={candidate.sky_exposure:.2f} > max={sky_exposure_max:.2f}",
                )
            )

        if effective_open_space < open_space_min:
            feasible = False
            checks.append(
                ConstraintCheck(
                    rule_key="open_space_min",
                    rule_type="hard",
                    passed=False,
                    detail=f"open_space={effective_open_space:.2f} < min={open_space_min:.2f}",
                )
            )

        if occupancy_type in {"residential", "mixed_use"} and actual_block_count < 2:
            feasible = False
            checks.append(
                ConstraintCheck(
                    rule_key="residential_multi_block",
                    rule_type="hard",
                    passed=False,
                    detail="residential program requires at least 2 blocks inside site boundary",
                )
            )

        if occupancy_type in {"residential", "mixed_use"} and candidate.building_spacing_m < defaults["min_building_spacing"]:
            feasible = False
            checks.append(
                ConstraintCheck(
                    rule_key="min_building_spacing",
                    rule_type="hard",
                    passed=False,
                    detail=f"spacing={candidate.building_spacing_m:.2f}m < min={defaults['min_building_spacing']:.2f}m",
                )
            )

        if user_far_min is not None and effective_far < user_far_min:
            feasible = False
            checks.append(
                ConstraintCheck(
                    rule_key="user_min_far",
                    rule_type="hard",
                    passed=False,
                    detail=f"far={effective_far:.2f} < min={user_far_min}",
                )
            )

        if user_qualitative_min is not None and qualitative["total"] < user_qualitative_min:
            feasible = False
            checks.append(
                ConstraintCheck(
                    rule_key="qualitative_min",
                    rule_type="hard",
                    passed=False,
                    detail=f"qualitative={qualitative['total']:.2f} < min={user_qualitative_min}",
                )
            )
        checks_ms += perf_counter() - t_step

        score = _score_candidate(candidate_for_quality, qualitative["total"]) if feasible else -1e6

        options.append(
            {
                "option_type": candidate.option_type,
                "score": round(score, 4),
                "parameters": {
                    "engine_version": "residential-multi-block-v2-boundary-fit",
                    "far": round(effective_far, 2),
                    "height_m": round(candidate.height, 2),
                    "coverage_percent": round(effective_coverage, 2),
                    "open_space_percent": round(effective_open_space, 2),
                    "block_count": actual_block_count,
                    "floors": candidate.floors,
                    "building_spacing_m": round(candidate.building_spacing_m, 2),
                    "max_block_length_m": round(candidate.max_block_length_m, 2),
                    "plan_family": candidate.plan_family,
                    "avg_unit_area_m2": round(candidate.avg_unit_area_m2, 2),
                    "unit_mix": candidate.unit_mix,
                    "qualitative_scores": qualitative,
                    "objective": objective,
                    "feasible": feasible,
                    "legal_basis_tags": _legal_basis(country_code, occupancy_type),
                },
                "checks": [item.model_dump() for item in checks],
                "mesh_payload": mesh_payload,
            }
        )

    timings["mesh_build_ms"] = round(mesh_ms * 1000.0, 3)
    timings["qualitative_eval_ms"] = round(qualitative_ms * 1000.0, 3)
    timings["constraint_checks_ms"] = round(checks_ms * 1000.0, 3)
    t_phase = perf_counter()
    options.sort(key=lambda item: item["score"], reverse=True)
    timings["sort_ms"] = round((perf_counter() - t_phase) * 1000.0, 3)
    timings["total_ms"] = round((perf_counter() - t_total) * 1000.0, 3)
    return options, timings


def compute_solar_profile(latitude: float, longitude: float, evaluation_date: date, hours: list[int]) -> list[dict]:
    day_of_year = evaluation_date.timetuple().tm_yday
    decl = 23.44 * sin((2 * pi / 365.0) * (day_of_year - 81))
    longitude_shift = (longitude - 127.0) / 30.0
    results: list[dict] = []

    for hour in hours:
        hour_angle = ((hour + longitude_shift) - 12) * 15
        altitude = max(0.0, 52.0 * cos((hour_angle / 180.0) * pi) * (1 - abs(latitude) / 130.0) + (decl / 2.8))
        azimuth = (180.0 + hour_angle) % 360.0
        insolation = max(0.0, altitude / 90.0) * 0.95
        shadow_ratio = max(0.0, min(1.0, 1.0 - altitude / 72.0))
        results.append(
            {
                "timestamp_utc": datetime.combine(evaluation_date, time(hour=hour, minute=0, tzinfo=timezone.utc)),
                "sun_altitude": round(altitude, 3),
                "sun_azimuth": round(azimuth, 3),
                "insolation_kwh_m2": round(insolation, 4),
                "shadow_ratio": round(shadow_ratio, 4),
            }
        )

    return results
