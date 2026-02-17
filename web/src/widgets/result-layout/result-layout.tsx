import { ArrowLeft, Sun, View } from 'lucide-react'
import { BuildingViewer, OptionCards, RunRead, SolarList } from '@/entities/run'
import { Button, StatusChip, Surface } from '@/shared/ui'

type ResultLayoutProps = {
  run: RunRead
  selectedOptionId: string | null
  onSelectOption: (id: string) => void
  onBack: () => void
}

export function ResultLayout({ run, selectedOptionId, onSelectOption, onBack }: ResultLayoutProps): JSX.Element {
  const fallbackOptionId = run.options[0]?.id ?? null
  const effectiveOptionId = selectedOptionId ?? fallbackOptionId
  const selectedOption = run.options.find((option) => option.id === effectiveOptionId) ?? run.options[0]
  const selectedSolar = selectedOption ? run.solar[selectedOption.id] ?? [] : []
  const qualitative = selectedOption?.parameters.qualitative_scores ?? {
    skyline_harmony: 0,
    street_scale_fit: 0,
    open_space_quality: 0,
    reference_maturity: 0,
    total: 0
  }
  const legalBasisTags = selectedOption?.parameters.legal_basis_tags ?? []
  const runtimeProfile = selectedOption?.parameters.runtime_profile

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 via-white to-amber-50 p-4 md:p-6">
      <div className="mx-auto max-w-[1400px] space-y-4">
        <Surface className="flex flex-wrap items-center justify-between gap-3 px-5 py-4">
          <div>
            <p className="text-xs uppercase tracking-[0.1em] text-slate-500">Result</p>
            <h1 className="text-xl font-semibold tracking-tight">설계 결과 대시보드</h1>
          </div>
          <div className="flex items-center gap-2">
            <StatusChip tone="good">Run {run.status}</StatusChip>
            <Button variant="secondary" onClick={onBack} className="gap-2">
              <ArrowLeft size={16} />
              입력 화면으로
            </Button>
          </div>
        </Surface>

        <Surface className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold tracking-tight">대안 비교</h2>
            <p className="text-sm text-slate-500">Run ID: {run.id}</p>
          </div>
          <OptionCards options={run.options} selectedId={effectiveOptionId} onSelect={onSelectOption} />
        </Surface>

        <div className="grid gap-4 xl:grid-cols-2">
          <Surface className="space-y-3">
            <div className="flex items-center gap-2 text-slate-900">
              <View size={18} className="text-sky-600" />
              <h3 className="text-lg font-semibold">3D 매스</h3>
            </div>
            <BuildingViewer mesh={selectedOption?.mesh_payload} />
          </Surface>

          <Surface className="space-y-3">
            <div className="flex items-center gap-2 text-slate-900">
              <Sun size={18} className="text-amber-500" />
              <h3 className="text-lg font-semibold">시간대 일조량</h3>
            </div>
            <SolarList points={selectedSolar} />
          </Surface>
        </div>

        {selectedOption ? (
          <Surface>
            <h3 className="mb-3 text-lg font-semibold">선택안 핵심 지표</h3>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="text-xs uppercase tracking-[0.08em] text-slate-500">FAR</p>
                <p className="mt-1 text-2xl font-semibold">{selectedOption.parameters.far ?? '-'}</p>
              </div>
              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="text-xs uppercase tracking-[0.08em] text-slate-500">Height</p>
                <p className="mt-1 text-2xl font-semibold">{selectedOption.parameters.height_m ?? '-'}m</p>
              </div>
              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="text-xs uppercase tracking-[0.08em] text-slate-500">Coverage</p>
                <p className="mt-1 text-2xl font-semibold">{selectedOption.parameters.coverage_percent ?? '-'}%</p>
              </div>
            </div>
            <div className="mt-3 rounded-2xl bg-slate-50 p-4">
              <p className="text-xs uppercase tracking-[0.08em] text-slate-500">Qualitative</p>
              <p className="mt-1 text-2xl font-semibold">{qualitative.total}</p>
              <p className="mt-1 text-sm text-slate-600">
                Skyline {qualitative.skyline_harmony} / Street {qualitative.street_scale_fit} / Open-space {qualitative.open_space_quality}
              </p>
              {typeof qualitative.market_fit === 'number' ? (
                <p className="mt-1 text-sm text-slate-600">Market-fit {qualitative.market_fit}</p>
              ) : null}
              {selectedOption.parameters.engine_version ? (
                <p className="mt-1 text-xs text-slate-500">Engine {selectedOption.parameters.engine_version}</p>
              ) : null}
            </div>
            <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-700">
                <p className="text-xs uppercase tracking-[0.08em] text-slate-500">배치 정보</p>
                <p className="mt-1">동 수: {selectedOption.parameters.block_count ?? '-'}</p>
                <p>대표 층수: {selectedOption.parameters.floors ?? '-'}층</p>
                <p>동간거리: {selectedOption.parameters.building_spacing_m ?? '-'}m</p>
              </div>
              <div className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-700">
                <p className="text-xs uppercase tracking-[0.08em] text-slate-500">주거 상품성</p>
                <p className="mt-1">평면 유형: {selectedOption.parameters.plan_family ?? '-'}</p>
                <p>평균 세대면적: {selectedOption.parameters.avg_unit_area_m2 ?? '-'}㎡</p>
                <p>주요 세대믹스: {selectedOption.parameters.unit_mix ? Object.keys(selectedOption.parameters.unit_mix).join(' / ') : '-'}</p>
              </div>
            </div>
          </Surface>
        ) : null}

        <Surface>
          <h3 className="mb-3 text-lg font-semibold">적용 제약 체크</h3>
          {selectedOption ? (
            <div className="space-y-2">
              {selectedOption.checks.map((check, index) => (
                <div key={`${check.rule_key}-${index}`} className="flex items-center justify-between rounded-xl border border-slate-200 p-3 text-sm">
                  <div>
                    <p className="font-medium text-slate-900">{check.rule_key}</p>
                    <p className="text-slate-500">{check.detail}</p>
                  </div>
                  <StatusChip tone={check.passed ? 'good' : 'warn'}>{check.passed ? 'Pass' : 'Fail'}</StatusChip>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500">표시할 제약 정보가 없습니다.</p>
          )}
        </Surface>

        {legalBasisTags.length > 0 ? (
          <Surface>
            <h3 className="mb-3 text-lg font-semibold">법규 근거 태그</h3>
            <div className="flex flex-wrap gap-2">
              {legalBasisTags.map((tag: string) => (
                <StatusChip key={tag} tone="neutral">
                  {tag}
                </StatusChip>
              ))}
            </div>
          </Surface>
        ) : null}

        {runtimeProfile ? (
          <Surface>
            <h3 className="mb-3 text-lg font-semibold">성능 프로파일</h3>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="mb-2 text-xs uppercase tracking-[0.08em] text-slate-500">Pipeline (ms)</p>
                <div className="space-y-1 text-sm text-slate-700">
                  {Object.entries(runtimeProfile.pipeline_ms ?? {}).map(([key, value]) => (
                    <p key={key}>
                      {key}: {value.toFixed(2)}
                    </p>
                  ))}
                </div>
              </div>
              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="mb-2 text-xs uppercase tracking-[0.08em] text-slate-500">Optimizer (ms)</p>
                <div className="space-y-1 text-sm text-slate-700">
                  {Object.entries(runtimeProfile.optimizer_ms ?? {}).map(([key, value]) => (
                    <p key={key}>
                      {key}: {value.toFixed(2)}
                    </p>
                  ))}
                </div>
              </div>
            </div>
          </Surface>
        ) : null}
      </div>
    </div>
  )
}
