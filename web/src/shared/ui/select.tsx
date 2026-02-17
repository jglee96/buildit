import { SelectHTMLAttributes } from 'react'
import { cn } from '@/shared/lib/cn'

export function Select({ className, ...props }: SelectHTMLAttributes<HTMLSelectElement>): JSX.Element {
  return (
    <select
      className={cn(
        'h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm text-slate-900 outline-none transition focus:border-slate-300 focus:ring-4 focus:ring-slate-100',
        className
      )}
      {...props}
    />
  )
}
