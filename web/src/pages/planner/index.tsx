import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PlannerFormValues, useProjectEvaluation } from '@/features/project-evaluation'
import { PlannerLayout } from '@/widgets/planner-layout'

const initialValues: PlannerFormValues = {
  email: 'demo@buildit.ai',
  projectName: 'jongno-mixed-use',
  occupancyType: 'residential',
  countryCode: 'KR',
  jurisdictionCode: 'KR-11-SEOUL-JONGNO',
  farMin: '300',
  farMax: '550',
  heightMax: '72',
  qualitativeMin: '70',
  evaluationDate: '2026-02-10',
  aestheticGoal: '보행 스케일을 해치지 않고 주변 스카이라인과 조화되는 단계형 매스',
  aestheticReferences: ''
}

export function PlannerPage(): JSX.Element {
  const navigate = useNavigate()
  const [values, setValues] = useState<PlannerFormValues>(initialValues)
  const [polygon, setPolygon] = useState<number[][][]>([])
  const { evaluate, loading, error } = useProjectEvaluation()

  const patchValues = (patch: Partial<PlannerFormValues>): void => {
    setValues((prev) => ({ ...prev, ...patch }))
  }

  const handleEvaluate = async (): Promise<void> => {
    const runId = await evaluate(values, polygon)
    navigate(`/results/${runId}`)
  }

  return (
    <PlannerLayout
      values={values}
      polygon={polygon}
      loading={loading}
      error={error}
      onValuesChange={patchValues}
      onPolygonChange={setPolygon}
      onEvaluate={handleEvaluate}
    />
  )
}
