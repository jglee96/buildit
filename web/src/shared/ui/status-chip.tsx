import { ReactNode } from 'react'
import { cn } from '@/shared/lib/cn'

type StatusChipProps = {
  tone: 'neutral' | 'good' | 'warn'
  children: ReactNode
}

const toneStyle = {
  neutral: 'bg-slate-100 text-slate-700',
  good: 'bg-emerald-100 text-emerald-700',
  warn: 'bg-amber-100 text-amber-700'
}

export function StatusChip({ tone, children }: StatusChipProps): JSX.Element {
  return <span className={cn('inline-flex h-7 items-center rounded-full px-3 text-xs font-medium', toneStyle[tone])}>{children}</span>
}
