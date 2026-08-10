import React from 'react'
import { Timer, AlertTriangle, CheckCircle, TrendingDown } from 'lucide-react'

interface RunwayCardProps {
  days: number | null
  balance: number
  dailyBurn: number
  status: string
  loading?: boolean
}

export default function RunwayCard({ days, balance, dailyBurn, status, loading }: RunwayCardProps) {
  if (loading) {
    return (
      <div className="card animate-pulse">
        <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-24 mb-4" />
        <div className="h-10 bg-slate-200 dark:bg-slate-700 rounded w-20 mb-3" />
        <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-32" />
      </div>
    )
  }

  const statusConfig = {
    healthy: { color: 'text-green-500', bg: 'bg-green-50 dark:bg-green-900/20', icon: CheckCircle, label: 'Healthy' },
    good: { color: 'text-blue-500', bg: 'bg-blue-50 dark:bg-blue-900/20', icon: CheckCircle, label: 'Good' },
    warning: { color: 'text-amber-500', bg: 'bg-amber-50 dark:bg-amber-900/20', icon: AlertTriangle, label: 'Warning' },
    critical: { color: 'text-red-500', bg: 'bg-red-50 dark:bg-red-900/20', icon: AlertTriangle, label: 'Critical' },
    unknown: { color: 'text-slate-400', bg: 'bg-slate-50 dark:bg-slate-800', icon: Timer, label: 'No Data' },
    no_expenses: { color: 'text-slate-400', bg: 'bg-slate-50 dark:bg-slate-800', icon: Timer, label: 'No Expenses' },
  }

  const cfg = statusConfig[status as keyof typeof statusConfig] || statusConfig.unknown
  const Icon = cfg.icon

  const formatCurrency = (n: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n)

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Runway</h3>
        <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${cfg.bg} ${cfg.color}`}>
          <Icon size={14} />
          {cfg.label}
        </span>
      </div>

      {days !== null ? (
        <>
          <div className="flex items-baseline gap-1 mb-1">
            <span className="text-4xl font-bold text-slate-900 dark:text-white">{days}</span>
            <span className="text-sm text-slate-500 dark:text-slate-400">days</span>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            of runway at {formatCurrency(dailyBurn)}/day burn rate
          </p>
          {days < 60 && (
            <div className="mt-3 flex items-center gap-2 text-xs text-amber-600 dark:text-amber-400">
              <TrendingDown size={14} />
              <span>Consider reducing discretionary spending</span>
            </div>
          )}
        </>
      ) : (
        <div className="py-4 text-center text-slate-400 dark:text-slate-500">
          <Timer size={32} className="mx-auto mb-2 opacity-50" />
          <p className="text-sm">
            {status === 'no_expenses' ? 'No expenses tracked yet' : 'Start adding transactions to see your runway'}
          </p>
        </div>
      )}
    </div>
  )
}
