from __future__ import annotations

from datetime import date, datetime, timezone

from app.core.database import Base, SessionLocal, engine
from app.schemas import EvaluateRequest, ProjectCreate, RequirementValue, RuleDefinitionCreate, RuleSetCreate
from app.services.orchestrator import (
    create_project,
    create_rule_definition,
    create_ruleset,
    create_user,
    get_run_response,
    run_evaluation,
    upsert_requirements,
)


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user = create_user(db, email="demo@buildit.ai", name="Demo User")
        project = create_project(
            db,
            ProjectCreate(
                user_id=user.id,
                name="jongno-office-test",
                country_code="KR",
                jurisdiction_code="KR-11-SEOUL-JONGNO",
                occupancy_type="office",
                site_geojson={
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [126.9792, 37.5725],
                            [126.9803, 37.5725],
                            [126.9803, 37.5732],
                            [126.9792, 37.5732],
                            [126.9792, 37.5725],
                        ]
                    ],
                },
            ),
        )
        rule_set = create_ruleset(
            db,
            RuleSetCreate(
                country_code="KR",
                jurisdiction_code="KR-11-SEOUL-JONGNO",
                category="zoning",
                version="2026.02.01",
                effective_from=date(2026, 2, 1),
                source_url="https://example.go.kr/notice/2026-02-01",
                source_hash="sha256:demo",
                published_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
                status="active",
            ),
        )
        create_rule_definition(
            db,
            RuleDefinitionCreate(
                rule_set_id=rule_set.id,
                rule_key="max_far",
                rule_type="hard",
                expression={"op": "lte", "field": "far", "value": 500},
                priority=10,
            ),
        )
        create_rule_definition(
            db,
            RuleDefinitionCreate(
                rule_set_id=rule_set.id,
                rule_key="max_height",
                rule_type="hard",
                expression={"op": "lte", "field": "height", "value": 72},
                priority=20,
            ),
        )
        upsert_requirements(
            db,
            project_id=project.id,
            requirements=[
                RequirementValue(key="far", min_value=320, max_value=560, unit="%"),
                RequirementValue(key="height", max_value=70, unit="m"),
            ],
        )
        run = run_evaluation(
            db,
            project=project,
            payload=EvaluateRequest(evaluation_date=date(2026, 2, 10), category="zoning", objective="maximize_far"),
        )
        response = get_run_response(db, run.id)
        print({"user_id": user.id, "project_id": project.id, "run_id": run.id, "top_option": response.options[0].parameters if response else None})
    finally:
        db.close()


if __name__ == "__main__":
    main()
