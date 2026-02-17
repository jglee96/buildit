import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { RunRead } from '@/entities/run'
import { getRun } from '@/shared/api/client'
import { Surface } from '@/shared/ui'
import { ResultLayout } from '@/widgets/result-layout'

export function ResultPage(): JSX.Element {
  const { runId } = useParams<{ runId: string }>()
  const navigate = useNavigate()
  const [run, setRun] = useState<RunRead | null>(null)
  const [selectedOptionId, setSelectedOptionId] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!runId) {
      setError('runId가 없습니다.')
      setLoading(false)
      return
    }

    const runFetch = async (): Promise<void> => {
      setLoading(true)
      setError('')
      try {
        const data = await getRun(runId)
        setRun(data)
        setSelectedOptionId(data.options[0]?.id ?? null)
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : '결과를 불러오지 못했습니다.')
      } finally {
        setLoading(false)
      }
    }

    runFetch()
  }, [runId])

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-100 p-6">
        <div className="mx-auto max-w-[1400px]">
          <Surface>
            <p className="text-sm text-slate-600">결과를 불러오는 중입니다...</p>
          </Surface>
        </div>
      </div>
    )
  }

  if (error || !run) {
    return (
      <div className="min-h-screen bg-slate-100 p-6">
        <div className="mx-auto max-w-[1400px]">
          <Surface className="space-y-4">
            <p className="text-sm text-rose-700">{error || '결과가 없습니다.'}</p>
            <button
              type="button"
              onClick={() => navigate('/')}
              className="inline-flex h-10 items-center rounded-xl bg-slate-900 px-4 text-sm font-semibold text-white"
            >
              입력 화면으로 돌아가기
            </button>
          </Surface>
        </div>
      </div>
    )
  }

  return <ResultLayout run={run} selectedOptionId={selectedOptionId} onSelectOption={setSelectedOptionId} onBack={() => navigate('/')} />
}
