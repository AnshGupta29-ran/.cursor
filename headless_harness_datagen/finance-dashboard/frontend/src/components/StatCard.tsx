import React from 'react'

interface StatCardProps {
  title: string
  value: string
  subtitle?: string
  icon: React.ReactNode
  color?: 'green' | 'red' | 'blue' | 'amber' | 'purple'
  trend?: { direction: 'up' | 'down'; value: string }
  loading?: boolean
}

const COLOR_CLASSES = {
  green: { bg: 'bg-green-50 dark:bg-green-900/20', text: 'text-green-600 dark:text-green-400', icon: 'text-green-500' },
  red: { bg: 'bg-red-50 dark:bg-red-900/20', text: 'text-red-600 dark:text-red-400', icon: 'text-red-500' },
  blue: { bg: 'bg-blue-50 dark:bg-blue-900/20', text: 'text-blue-600 dark:text-blue-400', icon: 'text-blue-500' },
  amber: { bg: 'bg-amber-50 dark:bg-amber-900/20', text: 'text-amber-600 dark:text-amber-400', icon: 'text-amber-500' },
  purple: { bg: 'bg-purple-50 dark:bg-purple-900/20', text: 'text-purple-600 dark:text-purple-400', icon: 'text-purple-500' },
}

export default function StatCard({ title, value, subtitle, icon, color = 'blue', trend, loading }: StatCardProps) {
  const c = COLOR_CLASSES[color]

  if (loading) {
    return (
      <div className="card animate-pulse">
        <div className="flex items-start justify-between">
          <div className="space-y-3 flex-1">
            <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-24" />
            <div className="h-8 bg-slate-200 dark:bg-slate-700 rounded w-32" />
            <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-20" />
          </div>
          <div className="w-12 h-12 rounded-xl bg-slate-200 dark:bg-slate-700" />
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{title}</p>
          <p className={`stat-value ${trend && trend.direction === 'down' ? 'text-red-600 dark:text-red-400' : 'text-slate-900 dark:text-white'}`}>
            {value}
          </p>
          {subtitle && (
            <p className="text-xs text-slate-400 dark:text-slate-500">{subtitle}</p>
          )}
          {trend && (
            <p className={`text-xs font-medium ${trend.direction === 'up' ? 'text-green-500' : 'text-red-500'}`}>
              {trend.direction === 'up' ? '↑' : '↓'} {trend.value}
            </p>
          )}
        </div>
        <div className={`w-12 h-12 rounded-xl ${c.bg} flex items-center justify-center ${c.icon}`}>
          {icon}
        </div>
      </div>
    </div>
  )
}
