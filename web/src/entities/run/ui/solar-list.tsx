import { SolarPoint } from '@/entities/run/model/types'

type SolarListProps = {
  points: SolarPoint[]
}

export function SolarList({ points }: SolarListProps): JSX.Element {
  if (points.length === 0) {
    return <p className="rounded-2xl border border-dashed border-slate-200 p-6 text-sm text-slate-500">아직 일조 데이터가 없습니다.</p>
  }

  return (
    <div className="space-y-2">
      {points.map((point) => (
        <div key={point.timestamp_utc} className="grid grid-cols-4 items-center rounded-xl bg-slate-50 px-3 py-3 text-xs text-slate-700 sm:text-sm">
          <span>{new Date(point.timestamp_utc).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}</span>
          <span>고도 {point.sun_altitude.toFixed(1)}°</span>
          <span>일사 {point.insolation_kwh_m2.toFixed(3)}</span>
          <span>음영 {Math.round(point.shadow_ratio * 100)}%</span>
        </div>
      ))}
    </div>
  )
}
