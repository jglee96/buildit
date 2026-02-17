import { useState } from 'react'
import {
  createProject,
  createRuleDefinition,
  createRuleSet,
  createUser,
  runEvaluation,
  setRequirements
} from '@/shared/api/client'
import { PlannerFormValues } from '@/features/project-evaluation/model/types'

const defaultHours = [9, 12, 15]

const countryRuleTemplate: Record<string, { sourceUrl: string; coverageMax: number; skyExposureMax: number; openSpaceMin: number }> = {
  KR: {
    sourceUrl: 'https://www.law.go.kr/%EB%B2%95%EB%A0%B9/%EA%B5%AD%ED%86%A0%EC%9D%98%EA%B3%84%ED%9A%8D%EB%B0%8F%EC%9D%B4%EC%9A%A9%EC%97%90%EA%B4%80%ED%95%9C%EB%B2%95%EB%A5%A0%EC%8B%9C%ED%96%89%EB%A0%B9/%EC%A0%9C85%EC%A1%B0',
    coverageMax: 60,
    skyExposureMax: 0.68,
    openSpaceMin: 22
  },
  SG: {
    sourceUrl: 'https://www.ura.gov.sg/Corporate/Guidelines/Development-Control',
    coverageMax: 50,
    skyExposureMax: 0.72,
    openSpaceMin: 28
  },
  'US-NYC': {
    sourceUrl: 'https://www.nyc.gov/site/planning/zoning/districts-tools/floor-area-ratio.page',
    coverageMax: 68,
    skyExposureMax: 0.78,
    openSpaceMin: 20
  }
}

type UseProjectEvaluationResult = {
  loading: boolean
  error: string
  evaluate: (form: PlannerFormValues, polygon: number[][][]) => Promise<string>
}

export function useProjectEvaluation(): UseProjectEvaluationResult {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const evaluate = async (form: PlannerFormValues, polygon: number[][][]): Promise<string> => {
    setLoading(true)
    setError('')
    try {
      const template = countryRuleTemplate[form.countryCode] ?? countryRuleTemplate.KR
      const references = form.aestheticReferences
        .split('\\n')
        .map((item) => item.trim())
        .filter(Boolean)

      const user = await createUser(form.email, 'Web User')

      const ruleSet = await createRuleSet({
        country_code: form.countryCode,
        jurisdiction_code: form.jurisdictionCode,
        category: 'zoning',
        version: `web-${Date.now()}`,
        effective_from: form.evaluationDate,
        effective_to: null,
        source_url: template.sourceUrl,
        source_hash: 'sha256:web',
        published_at: `${form.evaluationDate}T00:00:00Z`,
        status: 'active'
      })

      await Promise.all([
        createRuleDefinition({
          rule_set_id: ruleSet.id,
          rule_key: 'max_far',
          rule_type: 'hard',
          expression: { op: 'lte', field: 'far', value: Number(form.farMax) },
          priority: 10
        }),
        createRuleDefinition({
          rule_set_id: ruleSet.id,
          rule_key: 'max_height',
          rule_type: 'hard',
          expression: { op: 'lte', field: 'height', value: Number(form.heightMax) },
          priority: 20
        }),
        createRuleDefinition({
          rule_set_id: ruleSet.id,
          rule_key: 'max_coverage',
          rule_type: 'hard',
          expression: { op: 'lte', field: 'coverage', value: template.coverageMax },
          priority: 30
        }),
        createRuleDefinition({
          rule_set_id: ruleSet.id,
          rule_key: 'max_sky_exposure',
          rule_type: 'hard',
          expression: { op: 'lte', field: 'sky_exposure', value: template.skyExposureMax },
          priority: 40
        }),
        createRuleDefinition({
          rule_set_id: ruleSet.id,
          rule_key: 'min_open_space',
          rule_type: 'soft',
          expression: { op: 'gte', field: 'open_space', value: template.openSpaceMin },
          priority: 50
        })
      ])

      const project = await createProject({
        user_id: user.id,
        name: form.projectName,
        country_code: form.countryCode,
        jurisdiction_code: form.jurisdictionCode,
        occupancy_type: form.occupancyType,
        site_geojson: {
          type: 'Polygon',
          coordinates: polygon
        },
        aesthetic_inputs: [
          {
            category: 'design_goal',
            content: form.aestheticGoal || '도시 맥락과 조화되는 매스',
            reference_url: null,
            weight: 1.0
          },
          ...references.map((referenceUrl) => ({
            category: 'reference',
            content: '사용자 레퍼런스',
            reference_url: referenceUrl,
            weight: 1.1
          }))
        ]
      })

      await setRequirements(project.id, [
        { key: 'far', min_value: Number(form.farMin), max_value: Number(form.farMax), required_value: null, unit: '%' },
        { key: 'height', min_value: null, max_value: Number(form.heightMax), required_value: null, unit: 'm' },
        { key: 'qualitative_min', min_value: Number(form.qualitativeMin), max_value: null, required_value: null, unit: 'score' }
      ])

      const run = await runEvaluation(project.id, {
        evaluation_date: form.evaluationDate,
        category: 'zoning',
        objective: 'maximize_far',
        hours: defaultHours
      })

      return run.id
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : '평가 중 오류가 발생했습니다.'
      setError(message)
      throw caught
    } finally {
      setLoading(false)
    }
  }

  return { loading, error, evaluate }
}
