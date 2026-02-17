import { ReactNode } from 'react'
import { cn } from '@/shared/lib/cn'

type FieldProps = {
  label: string
  hint?: string
  children: ReactNode
  className?: string
}

export function Field({ label, hint, children, className }: FieldProps): JSX.Element {
  return (
    <div className={cn('space-y-1.5', className)}>
      <label className="block text-xs font-medium uppercase tracking-[0.08em] text-slate-500">{label}</label>
      {children}
      {hint ? <p className="text-xs text-slate-500">{hint}</p> : null}
    </div>
  )
}
