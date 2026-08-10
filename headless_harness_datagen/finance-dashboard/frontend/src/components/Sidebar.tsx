import React from 'react'
import { useTheme } from '../context/ThemeContext'
import {
  LayoutDashboard, ArrowRightLeft, PiggyBank, BarChart3,
  Moon, Sun, Plus,
} from 'lucide-react'

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'transactions', label: 'Transactions', icon: ArrowRightLeft },
  { id: 'budgets', label: 'Budgets', icon: PiggyBank },
  { id: 'analytics', label: 'Analytics', icon: BarChart3 },
]

interface SidebarProps {
  active: string
  onNavigate: (page: string) => void
  onAddTransaction: () => void
}

export default function Sidebar({ active, onNavigate, onAddTransaction }: SidebarProps) {
  const { theme, toggle } = useTheme()

  return (
    <aside className="fixed left-0 top-0 h-full w-64 bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 flex flex-col z-20">
      {/* Logo */}
      <div className="p-6 border-b border-slate-200 dark:border-slate-700">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center text-white font-bold text-lg">
            $
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-800 dark:text-white">Finance</h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">Dashboard</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {NAV_ITEMS.map(item => {
          const Icon = item.icon
          const isActive = active === item.id
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-150 ${
                isActive
                  ? 'bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700/50'
              }`}
            >
              <Icon size={20} />
              {item.label}
            </button>
          )
        })}
      </nav>

      {/* Add Transaction Button */}
      <div className="px-4 pb-4">
        <button
          onClick={onAddTransaction}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-lg text-sm font-medium transition-colors"
        >
          <Plus size={18} />
          Add Transaction
        </button>
      </div>

      {/* Theme Toggle */}
      <div className="p-4 border-t border-slate-200 dark:border-slate-700">
        <button
          onClick={toggle}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700/50 transition-colors"
        >
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          {theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
        </button>
      </div>
    </aside>
  )
}
