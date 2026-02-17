import { AlertTriangle, Building2, Compass, Sparkles } from 'lucide-react'
import { PlannerFormValues } from '@/features/project-evaluation'
import { SiteMap } from '@/features/site-drawing'
import { Button, Field, Input, Select, StatusChip, Surface, Textarea } from '@/shared/ui'

type PlannerLayoutProps = {
  values: PlannerFormValues
  polygon: number[][][]
  loading: boolean
  error: string
  onValuesChange: (patch: Partial<PlannerFormValues>) => void
  onPolygonChange: (nextPolygon: number[][][]) => void
  onEvaluate: () => void
}

export function PlannerLayout({
  values,
  polygon,
  loading,
  error,
  onValuesChange,
  onPolygonChange,
  onEvaluate
}: PlannerLayoutProps): JSX.Element {
  const canEvaluate = polygon.length > 0 && !loading

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 via-white to-sky-50 p-4 text-slate-900 md:p-6">
      <div className="mx-auto max-w-[1400px] space-y-4">
        <Surface className="flex flex-wrap items-center justify-between gap-3 px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-sky-100 text-sky-700">
              <Building2 size={20} />
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.12em] text-slate-500">Buildit</p>
              <h1 className="text-xl font-semibold tracking-tight">AI 건축 설계 플래너</h1>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <StatusChip tone="neutral">1. 대지 설정</StatusChip>
            <StatusChip tone="neutral">2. 조건 입력</StatusChip>
            <StatusChip tone="neutral">3. 결과 확인</StatusChip>
          </div>
        </Surface>

        <div className="grid gap-4 xl:grid-cols-[420px_1fr]">
          <Surface className="space-y-4 xl:sticky xl:top-4 xl:h-fit">
            <div className="space-y-1">
              <p className="text-lg font-semibold tracking-tight">설계 조건</p>
              <p className="text-sm text-slate-500">법규 기준일을 기준으로 적용 룰 버전을 고정해 계산합니다.</p>
            </div>

            <Field label="Email">
              <Input value={values.email} onChange={(event) => onValuesChange({ email: event.target.value })} />
            </Field>

            <Field label="프로젝트명">
              <Input value={values.projectName} onChange={(event) => onValuesChange({ projectName: event.target.value })} />
            </Field>

            <div className="grid gap-2 sm:grid-cols-2">
              <Field label="국가">
                <Select
                  value={values.countryCode}
                  onChange={(event) => {
                    const next = event.target.value
                    const jurisdictionDefaults: Record<string, string> = {
                      KR: 'KR-11-SEOUL-JONGNO',
                      SG: 'SG-CENTRAL',
                      'US-NYC': 'US-NYC-MANHATTAN'
                    }
                    onValuesChange({
                      countryCode: next,
                      jurisdictionCode: jurisdictionDefaults[next] ?? values.jurisdictionCode
                    })
                  }}
                >
                  <option value="KR">대한민국 (KR)</option>
                  <option value="SG">Singapore (SG)</option>
                  <option value="US-NYC">United States - NYC</option>
                </Select>
              </Field>
              <Field label="관할 코드">
                <Input value={values.jurisdictionCode} onChange={(event) => onValuesChange({ jurisdictionCode: event.target.value })} />
              </Field>
            </div>

            <Field label="건축물 유형">
              <Select value={values.occupancyType} onChange={(event) => onValuesChange({ occupancyType: event.target.value })}>
                <option value="residential">Residential</option>
                <option value="office">Office</option>
                <option value="commercial">Commercial</option>
                <option value="mixed_use">Mixed Use</option>
              </Select>
            </Field>

            <div className="grid gap-2 sm:grid-cols-3">
              <Field label="FAR Min">
                <Input value={values.farMin} type="number" onChange={(event) => onValuesChange({ farMin: event.target.value })} />
              </Field>
              <Field label="FAR Max">
                <Input value={values.farMax} type="number" onChange={(event) => onValuesChange({ farMax: event.target.value })} />
              </Field>
              <Field label="Height Max(m)">
                <Input value={values.heightMax} type="number" onChange={(event) => onValuesChange({ heightMax: event.target.value })} />
              </Field>
            </div>

            <Field label="정성 평가 최소점수" hint="도시 미관/맥락 점수 하한값">
              <Input
                value={values.qualitativeMin}
                type="number"
                min={0}
                max={100}
                onChange={(event) => onValuesChange({ qualitativeMin: event.target.value })}
              />
            </Field>

            <Field label="미관 목표">
              <Textarea
                value={values.aestheticGoal}
                onChange={(event) => onValuesChange({ aestheticGoal: event.target.value })}
                placeholder="예: 저층부는 보행 친화, 상부는 단계형 후퇴, 주변 스카이라인과 조화"
              />
            </Field>

            <Field label="레퍼런스 URL(줄바꿈 구분)" hint="정성 평가 참고 자료로 저장됩니다.">
              <Textarea
                value={values.aestheticReferences}
                onChange={(event) => onValuesChange({ aestheticReferences: event.target.value })}
                placeholder="https://...\nhttps://..."
              />
            </Field>

            <Field label="평가 기준일" hint="해당 날짜에 유효한 법규 버전으로 계산합니다.">
              <Input value={values.evaluationDate} type="date" onChange={(event) => onValuesChange({ evaluationDate: event.target.value })} />
            </Field>

            {error ? (
              <div className="flex items-start gap-2 rounded-2xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
                <AlertTriangle size={16} className="mt-0.5" />
                <p>{error}</p>
              </div>
            ) : null}

            <Button onClick={onEvaluate} disabled={!canEvaluate} className="w-full">
              {loading ? '계산 중...' : '결과 페이지로 이동하여 계산'}
            </Button>
          </Surface>

          <div className="space-y-4">
            <Surface>
              <div className="mb-3 flex items-center justify-between gap-2">
                <div>
                  <p className="text-lg font-semibold tracking-tight">대지 영역 입력</p>
                  <p className="text-sm text-slate-500">지도에서 폴리곤을 직접 그려 대지를 지정하세요.</p>
                </div>
                <div className="flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-600">
                  <Compass size={14} />
                  Map Ready
                </div>
              </div>
              <SiteMap polygon={polygon} onPolygonChange={onPolygonChange} />
            </Surface>

            <Surface className="flex items-start gap-3 bg-sky-50/80">
              <Sparkles className="mt-1 text-sky-600" size={18} />
              <div className="space-y-1 text-sm text-slate-700">
                <p className="font-medium text-slate-900">결과는 별도 페이지에서 확인됩니다.</p>
                <p>계산 완료 후 대안 3개 비교, 3D 매스, 시간대 일조량을 결과 화면에서 확인할 수 있습니다.</p>
              </div>
            </Surface>
          </div>
        </div>
      </div>
    </div>
  )
}
