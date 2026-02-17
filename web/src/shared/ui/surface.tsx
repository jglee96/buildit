import { HTMLAttributes } from 'react'
import { cn } from '@/shared/lib/cn'

export function Surface({ className, ...props }: HTMLAttributes<HTMLDivElement>): JSX.Element {
  return (
    <div
      className={cn(
        'rounded-3xl border border-slate-200/70 bg-white/85 p-5 shadow-sm backdrop-blur',
        className
      )}
      {...props}
    />
  )
}
