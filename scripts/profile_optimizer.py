from __future__ import annotations

import cProfile
import pstats
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.services.optimizer import optimize_options


def build_inputs() -> tuple[list, list, dict, list]:
    rule_definitions = [
        SimpleNamespace(rule_key='max_far', expression={'op': 'lte', 'field': 'far', 'value': 550}, rule_type='hard'),
        SimpleNamespace(rule_key='max_height', expression={'op': 'lte', 'field': 'height', 'value': 72}, rule_type='hard'),
        SimpleNamespace(rule_key='max_coverage', expression={'op': 'lte', 'field': 'coverage', 'value': 60}, rule_type='hard'),
        SimpleNamespace(rule_key='min_open_space', expression={'op': 'gte', 'field': 'open_space', 'value': 22}, rule_type='soft'),
    ]
    requirements = [
        SimpleNamespace(key='far', min_value=300.0, max_value=550.0),
        SimpleNamespace(key='height', min_value=None, max_value=72.0),
        SimpleNamespace(key='qualitative_min', min_value=60.0, max_value=None),
    ]
    site_geojson = {
        'type': 'Polygon',
        'coordinates': [
            [
                [126.9792, 37.5725],
                [126.9804, 37.5724],
                [126.9806, 37.5731],
                [126.9799, 37.5736],
                [126.9790, 37.5734],
                [126.9792, 37.5725],
            ]
        ],
    }
    aesthetic_inputs = [
        SimpleNamespace(content='주변 스카이라인과 조화', reference_url='https://example.com/ref1', weight=1.0),
        SimpleNamespace(content='보행 친화 저층부', reference_url='https://example.com/ref2', weight=1.1),
    ]
    return rule_definitions, requirements, site_geojson, aesthetic_inputs


def run_once() -> dict[str, float]:
    rule_definitions, requirements, site_geojson, aesthetic_inputs = build_inputs()
    options, timings = optimize_options(
        rule_definitions=rule_definitions,
        requirements=requirements,
        objective='maximize_far',
        site_geojson=site_geojson,
        country_code='KR',
        occupancy_type='residential',
        aesthetic_inputs=aesthetic_inputs,
    )
    _ = options[0]['score']
    return timings


def main() -> None:
    profiler = cProfile.Profile()
    profiler.enable()

    aggregated: dict[str, float] = {}
    runs = 80
    for _ in range(runs):
        timings = run_once()
        for key, value in timings.items():
            aggregated[key] = aggregated.get(key, 0.0) + value

    profiler.disable()

    print('Average optimizer timings (ms):')
    for key in sorted(aggregated.keys()):
        print(f'  {key}: {aggregated[key] / runs:.3f}')

    print('\nTop cProfile functions:')
    stats = pstats.Stats(profiler).sort_stats('cumtime')
    stats.print_stats(15)


if __name__ == '__main__':
    main()
