import { ButtonHTMLAttributes } from 'react'
import { cn } from '@/shared/lib/cn'

type ButtonVariant = 'primary' | 'secondary' | 'ghost'

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant
}

const variantStyles: Record<ButtonVariant, string> = {
  primary: 'bg-sky-600 text-white hover:bg-sky-700 focus-visible:ring-sky-300 disabled:bg-slate-300',
  secondary: 'bg-slate-100 text-slate-800 hover:bg-slate-200 focus-visible:ring-slate-300 disabled:bg-slate-100 disabled:text-slate-400',
  ghost: 'bg-transparent text-slate-700 hover:bg-slate-100 focus-visible:ring-slate-300 disabled:text-slate-400'
}

export function Button({ className, variant = 'primary', ...props }: ButtonProps): JSX.Element {
  return (
    <button
      className={cn(
        'inline-flex h-11 items-center justify-center rounded-xl px-4 text-sm font-semibold tracking-tight transition-colors focus-visible:outline-none focus-visible:ring-4 disabled:cursor-not-allowed',
        variantStyles[variant],
        className
      )}
      {...props}
    />
  )
}
