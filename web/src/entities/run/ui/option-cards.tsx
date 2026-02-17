import { RunOption } from '@/entities/run/model/types'
import { StatusChip } from '@/shared/ui'

type OptionCardsProps = {
  options: RunOption[]
  selectedId: string | null
  onSelect: (id: string) => void
}

export function OptionCards({ options, selectedId, onSelect }: OptionCardsProps): JSX.Element {
  return (
    <div className="grid grid-cols-1 gap-3 xl:grid-cols-3">
      {options.map((option) => {
        const isSelected = selectedId === option.id
        const isFeasible = option.parameters.feasible ?? true
        return (
          <button
            key={option.id}
            type="button"
            onClick={() => onSelect(option.id)}
            className={`rounded-2xl border p-4 text-left transition ${
              isSelected ? 'border-sky-300 bg-sky-50 ring-4 ring-sky-100' : 'border-slate-200 bg-white hover:border-slate-300'
            }`}
          >
            <div className="mb-3 flex items-center justify-between gap-2">
              <p className="text-sm font-semibold text-slate-900">{option.rank}. {option.option_type}</p>
              <StatusChip tone={isFeasible ? 'good' : 'warn'}>
                {isFeasible ? 'Feasible' : 'Review'}
              </StatusChip>
            </div>
            <p className="text-xs text-slate-500">Score {option.score.toFixed(1)}</p>
            <p className="mt-1 text-sm text-slate-700">FAR {option.parameters.far ?? '-'} / Height {option.parameters.height_m ?? '-'}m</p>
            {typeof option.parameters.block_count === 'number' ? (
              <p className="mt-1 text-xs text-slate-500">동 수 {option.parameters.block_count} / 층수 {option.parameters.floors ?? '-'}</p>
            ) : null}
          </button>
        )
      })}
    </div>
  )
}
