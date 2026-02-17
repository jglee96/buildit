import { useNavigate, useRouteError } from 'react-router-dom'
import { Button, Surface } from '@/shared/ui'

export function RouteError(): JSX.Element {
  const navigate = useNavigate()
  const error = useRouteError()
  const message = error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.'

  return (
    <div className="min-h-screen bg-slate-100 p-6">
      <div className="mx-auto max-w-[900px]">
        <Surface className="space-y-4">
          <h1 className="text-xl font-semibold">페이지 오류</h1>
          <p className="text-sm text-slate-600">{message}</p>
          <Button onClick={() => navigate('/')}>입력 화면으로 이동</Button>
        </Surface>
      </div>
    </div>
  )
}
