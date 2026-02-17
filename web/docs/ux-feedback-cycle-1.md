# Simulated Feedback Cycle 1

This is simulated interview analysis (not real user research).

## 1) Session Setup
- Product/version: buildit-web v0.2 (planner + result split)
- Persona: 초급 건축기획자, 촉박한 일정, 법규 해석 경험 낮음
- Scenario: 종로 대지를 입력하고 FAR 최대화를 위한 대안을 확인한다.
- Success criteria: 3분 이내에 대지 지정, 계산 실행, 결과 대안 1개 선택

## 2) Simulated Interview Notes
- First impression: 지도 영역과 입력 폼이 분리되어 구조는 이해 가능
- Key task journey: 지도 진입 -> 폴리곤 버튼 찾기 -> 조건 입력 -> 결과 이동
- Quotes:
  - "어디서 그리기를 시작하는지 바로 보여서 좋네요."
  - "결과 카드가 보이긴 하는데 숫자 해석이 조금 느립니다."
  - "대지가 제대로 입력됐는지 면적 정보가 있으면 확신이 들겠어요."

## 3) Friction Log
- Step: 대지 입력 직후
- Problem observed: 사용자가 폴리곤이 정상 입력되었는지 확신하지 못함
- Why it matters: 잘못된 대지로 계산을 실행할 가능성 증가
- Severity: High

- Step: 결과 비교
- Problem observed: 선택안의 핵심 수치(FAR/높이/건폐율)가 한눈에 정리되지 않음
- Why it matters: 대안 선택 시간이 길어짐
- Severity: Medium

## 4) Prioritized Improvements
- Change proposal: 지도 헤더에 정점 수/면적(㎡) 표시 추가
- Expected user impact: 대지 입력 완료 인지성 상승, 재작업 감소
- Effort: S
- Confidence: 88%
- Priority: P0

- Change proposal: 결과 페이지에 선택안 핵심지표 카드 추가
- Expected user impact: 대안 비교/의사결정 시간 단축
- Effort: S
- Confidence: 84%
- Priority: P1

- Change proposal: 입력 패널 sticky 처리로 긴 화면에서도 CTA 유지
- Expected user impact: 입력 중 스크롤 이탈 감소
- Effort: S
- Confidence: 76%
- Priority: P1

## 5) Next Iteration Plan
- What to change before next test: 상기 3개 개선 반영
- What to re-test: 초급 사용자 기준 대지 입력 완료율과 결과 선택 시간
- What success looks like next round: 첫 시도 성공률 90%+, 결과 선택 시간 30% 감소
