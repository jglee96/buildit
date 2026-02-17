# buildit

AI 기반 건축설계 웹 서비스 MVP.

이 버전은 다음 목표를 실제 동작 가능한 형태로 구현합니다.

- 지도에서 대지 영역(폴리곤) 입력
- 건축물 용도/사양 입력
- 날짜 기준(`evaluation_date`) 법규 버전 자동 선택
- 프로젝트별 룰 스냅샷 고정(재현성 확보)
- FAR 최대화 중심 3개 대안 산출
- Three.js 3D 매스 시각화
- 위치 기반 시간대 일조량(간이 모델) 계산
- 정성 평가(스카이라인/가로 스케일/오픈스페이스/레퍼런스 성숙도) 반영
- 국가 선택(KR/SG/US-NYC) 및 미관 레퍼런스 입력 지원
- 공동주택(`residential/mixed_use`)은 다동 배치(multi-block)로 생성하고 세대면적 믹스/동간거리/평면유형 점수 반영

## Architecture

- Backend: `FastAPI + SQLAlchemy`
- DB: `SQLite(기본)`, PostgreSQL 전환 가능
- Frontend: `React + Vite + TypeScript + Tailwind + shadcn-style primitives + MapLibre + Three.js`
- Frontend structure: `Feature-Sliced Design (app/pages/widgets/features/entities/shared)`
- Rule system:
  - `rule_sets`: 관할/카테고리/버전/시행일
  - `rule_definitions`: JSON DSL 기반 제약식
  - `project_rule_snapshots`: 실행 시점 룰 고정

## Backend Run

```bash
cd /Users/zakklee/dev/buildit
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app
```

API base: `http://127.0.0.1:8000/api`

`--reload` 옵션은 일부 제한된 터미널 환경에서 파일 감시 권한 오류가 발생할 수 있습니다.

## Frontend Run

```bash
cd /Users/zakklee/dev/buildit/web
npm install
npm run dev
```

Web URL: `http://localhost:5173`

## One-command Restart (Backend + Frontend)

```bash
cd /Users/zakklee/dev/buildit
./scripts/restart-dev.sh
```

Stop both:

```bash
cd /Users/zakklee/dev/buildit
./scripts/stop-dev.sh
```

### Web Flow

- 입력 페이지: `/`
- 결과 페이지: `/results/:runId`
- 지도 조작: `폴리곤 그리기` 버튼 클릭 후 대지 직접 드로잉

## Seed Demo Data

```bash
cd /Users/zakklee/dev/buildit
source .venv/bin/activate
python3 scripts/seed_demo.py
```

## Optimizer Profiling

```bash
cd /Users/zakklee/dev/buildit
source .venv/bin/activate
python3 scripts/profile_optimizer.py
```

## Core API Endpoints

- `POST /api/users`
- `POST /api/rules/sets`
- `POST /api/rules/definitions`
- `POST /api/projects`
- `POST /api/projects/{project_id}/requirements`
- `POST /api/projects/{project_id}/aesthetic-inputs`
- `POST /api/runs/projects/{project_id}/evaluate`
- `GET /api/runs/{run_id}`

## Policy-Change 대응 설계 포인트

- 법규는 코드가 아닌 DB 데이터로 관리
- 각 룰셋은 `effective_from/effective_to/version/source_url` 보유
- 계산 요청마다 `evaluation_date`를 받아 해당 시점 룰만 선택
- 계산 순간 `project_rule_snapshots`에 룰 ID 목록 고정
- 과거 결과를 동일 조건으로 재현 가능

## Notes

- 일조량 계산은 현재 간이 모델입니다. 향후 `pvlib + 주변 건물 3D`로 고도화 가능합니다.
- 최적화도 현재는 baseline heuristic입니다. 향후 MILP/NSGA-II 엔진으로 교체 권장.
- 법규 조사 메모: `docs/legal-research-2026-02-17.md`
