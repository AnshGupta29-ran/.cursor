export interface Transaction {
  id: number
  amount: number
  description: string
  category: string
  subcategory: string | null
  type: 'income' | 'expense'
  date: string
  created_at: string | null
}

export interface TransactionFormData {
  amount: number
  description: string
  category: string
  subcategory?: string
  type: 'income' | 'expense'
  date: string
}

export interface Budget {
  id: number
  category: string
  amount: number
  month: number
  year: number
  spent: number
  remaining: number
  percentage: number
}

export interface Summary {
  total_income: number
  total_expenses: number
  net: number
  balance: number
  transaction_count: number
  category_breakdown: { category: string; amount: number }[]
  monthly_trends: {
    month: number
    year: number
    income: number
    expenses: number
    net: number
  }[]
}

export interface Insights {
  velocity: {
    current_avg: number
    normal_avg: number
    is_elevated: boolean
    percentage: number
  }
  runway: {
    days: number | null
    balance: number
    daily_burn: number
    status: 'healthy' | 'good' | 'warning' | 'critical' | 'unknown' | 'no_expenses'
  }
  anomalies: {
    category: string
    current_week: number
    normal_weekly: number
    deviation: number
    is_overspend: boolean
    explanation: string
  }[]
  recurring: {
    description: string
    amount: number
    frequency: string
    months_seen: number
    total_spent: number
    category: string
  }[]
  dark_patterns: {
    description: string
    amount: number
    monthly_cost: number
    total_spent: number
    months_active: number
    risk_level: 'high' | 'medium'
    reason: string
  }[]
}

export interface PaginatedResponse<T> {
  transactions: T[]
  total: number
  pages: number
  page: number
  per_page: number
}

export const CATEGORIES = [
  'Housing', 'Food & Dining', 'Transportation', 'Utilities',
  'Entertainment', 'Healthcare', 'Shopping', 'Subscriptions',
  'Personal Care', 'Education', 'Travel', 'Income', 'Other',
] as const

export const SUBCATEGORIES: Record<string, string[]> = {
  Housing: ['Rent', 'Mortgage', 'Home Insurance', 'Repairs', 'HOA'],
  'Food & Dining': ['Groceries', 'Restaurants', 'Coffee Shops', 'Delivery'],
  Transportation: ['Gas', 'Car Insurance', 'Public Transit', 'Ride Share', 'Maintenance'],
  Utilities: ['Electricity', 'Water', 'Internet', 'Phone', 'Gas Bill'],
  Entertainment: ['Movies', 'Games', 'Streaming', 'Concerts', 'Sports'],
  Healthcare: ['Insurance', 'Doctor Visit', 'Pharmacy', 'Dental', 'Vision'],
  Shopping: ['Clothing', 'Electronics', 'Home Goods', 'Online Shopping'],
  Subscriptions: ['Netflix', 'Spotify', 'Cloud Storage', 'Gym', 'Domain Renewal'],
  'Personal Care': ['Haircut', 'Skincare', 'Salon', 'Spa'],
  Education: ['Tuition', 'Books', 'Courses', 'Certifications'],
  Travel: ['Flights', 'Hotels', 'Car Rental', 'Activities'],
  Income: ['Salary', 'Freelance', 'Investments', 'Gifts', 'Refunds'],
  Other: ['Miscellaneous', 'Bank Fees', 'ATM'],
}

export const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
]
