"""
Personal Finance Dashboard — Backend API
=========================================
Flask + SQLAlchemy + SQLite
Features: CRUD transactions, budgets, insights engine (velocity, runway, anomalies, recurring)
"""

import os
import random
import statistics
from collections import defaultdict
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

# ---------------------------------------------------------------------------
# App Configuration
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///finance.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
CORS(app)
db = SQLAlchemy(app)

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
CATEGORIES = [
    "Housing", "Food & Dining", "Transportation", "Utilities",
    "Entertainment", "Healthcare", "Shopping", "Subscriptions",
    "Personal Care", "Education", "Travel", "Income", "Other",
]

SUBCATEGORIES = {
    "Housing": ["Rent", "Mortgage", "Home Insurance", "Repairs", "HOA"],
    "Food & Dining": ["Groceries", "Restaurants", "Coffee Shops", "Delivery"],
    "Transportation": ["Gas", "Car Insurance", "Public Transit", "Ride Share", "Maintenance"],
    "Utilities": ["Electricity", "Water", "Internet", "Phone", "Gas Bill"],
    "Entertainment": ["Movies", "Games", "Streaming", "Concerts", "Sports"],
    "Healthcare": ["Insurance", "Doctor Visit", "Pharmacy", "Dental", "Vision"],
    "Shopping": ["Clothing", "Electronics", "Home Goods", "Online Shopping"],
    "Subscriptions": ["Netflix", "Spotify", "Cloud Storage", "Gym", "Domain Renewal"],
    "Personal Care": ["Haircut", "Skincare", "Salon", "Spa"],
    "Education": ["Tuition", "Books", "Courses", "Certifications"],
    "Travel": ["Flights", "Hotels", "Car Rental", "Activities"],
    "Income": ["Salary", "Freelance", "Investments", "Gifts", "Refunds"],
    "Other": ["Miscellaneous", "Bank Fees", "ATM"],
}


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    subcategory = db.Column(db.String(50), nullable=True)
    type = db.Column(db.String(10), nullable=False)  # "income" or "expense"
    date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "amount": self.amount,
            "description": self.description,
            "category": self.category,
            "subcategory": self.subcategory,
            "type": self.type,
            "date": self.date.isoformat(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Budget(db.Model):
    __tablename__ = "budgets"

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "category": self.category,
            "amount": self.amount,
            "month": self.month,
            "year": self.year,
        }


# ---------------------------------------------------------------------------
# Seed Data
# ---------------------------------------------------------------------------
def seed_database():
    """Populate the database with realistic sample transactions and budgets."""
    if Transaction.query.first() is not None:
        return  # Already seeded

    today = date.today()
    start_date = today - timedelta(days=90)

    # Budgets for current month
    current_month = today.month
    current_year = today.year
    budget_data = [
        ("Housing", 1400.0),
        ("Food & Dining", 600.0),
        ("Transportation", 300.0),
        ("Utilities", 250.0),
        ("Entertainment", 150.0),
        ("Healthcare", 200.0),
        ("Shopping", 300.0),
        ("Subscriptions", 80.0),
        ("Personal Care", 100.0),
        ("Education", 100.0),
    ]
    for cat, amt in budget_data:
        db.session.add(Budget(category=cat, amount=amt, month=current_month, year=current_year))

    # Also seed previous month's budgets
    prev_month = current_month - 1 if current_month > 1 else 12
    prev_year = current_year if current_month > 1 else current_year - 1
    for cat, amt in budget_data:
        db.session.add(Budget(category=cat, amount=amt, month=prev_month, year=prev_year))

    # Income: bi-weekly salary + occasional freelance
    current = start_date
    salary_dates = []
    while current <= today:
        salary_dates.append(current)
        current += timedelta(days=14)

    salary_count = 0
    for sd in salary_dates:
        salary_count += 1
        t = Transaction(
            amount=3200.0 if salary_count % 2 == 1 else 3100.0,
            description="Salary — TechCorp Inc.",
            category="Income",
            subcategory="Salary",
            type="income",
            date=sd,
        )
        db.session.add(t)

    # Occasional freelance income
    for _ in range(4):
        d = start_date + timedelta(days=random.randint(1, 89))
        db.session.add(Transaction(
            amount=round(random.uniform(200, 1500), 2),
            description=f"Freelance — {random.choice(['Web Dev', 'Consulting', 'Design', 'Writing'])}",
            category="Income",
            subcategory="Freelance",
            type="income",
            date=d,
        ))

    # Rent - 1st of each month
    for m_offset in range(4):
        m = start_date.month + m_offset
        y = start_date.year
        if m > 12:
            m -= 12
            y += 1
        rent_date = date(y, m, 1)
        if rent_date <= today:
            db.session.add(Transaction(
                amount=1200.0,
                description="Rent — Downtown Apt",
                category="Housing",
                subcategory="Rent",
                type="expense",
                date=rent_date,
            ))

    # Recurring subscriptions (monthly)
    subscriptions = [
        ("Netflix", 15.99, 8),
        ("Spotify", 9.99, 8),
        ("Cloud Storage", 9.99, 8),
        ("Gym Membership", 49.99, 8),
    ]
    for name, amt, day in subscriptions:
        for m_offset in range(4):
            m = start_date.month + m_offset
            y = start_date.year
            if m > 12:
                m -= 12
                y += 1
            sub_date = date(y, m, min(day, 28))
            if sub_date <= today:
                db.session.add(Transaction(
                    amount=amt,
                    description=name,
                    category="Subscriptions",
                    subcategory=name,
                    type="expense",
                    date=sub_date,
                ))

    # Regular expenses (groceries, dining, gas, utilities)
    expense_templates = [
        ("Groceries", "Food & Dining", "Groceries", 45.0, 120.0, 5),
        ("Dining Out", "Food & Dining", "Restaurants", 15.0, 60.0, 3),
        ("Gas Station", "Transportation", "Gas", 25.0, 55.0, 2),
        ("Coffee Shop", "Food & Dining", "Coffee Shops", 4.0, 8.0, 3),
        ("Uber/Lyft", "Transportation", "Ride Share", 8.0, 25.0, 1),
        ("Electric Bill", "Utilities", "Electricity", 65.0, 110.0, 1),
        ("Internet", "Utilities", "Internet", 74.99, 74.99, 1),
        ("Phone", "Utilities", "Phone", 45.0, 65.0, 1),
        ("Amazon Purchase", "Shopping", "Online Shopping", 10.0, 80.0, 2),
        ("Pharmacy", "Healthcare", "Pharmacy", 5.0, 40.0, 1),
    ]

    for desc, cat, sub, min_amt, max_amt, frequency in expense_templates:
        current = start_date
        while current <= today:
            # Skip some days based on frequency (every N days on average)
            if random.random() < (1.0 / max(1, 7 / frequency)):
                amt = round(random.uniform(min_amt, max_amt), 2)
                # Some variation to simulate real data
                if random.random() < 0.1:
                    amt *= random.uniform(1.5, 3.0)  # Occasional splurge
                db.session.add(Transaction(
                    amount=round(amt, 2),
                    description=desc if not cat == "Food & Dining" or desc == "Groceries"
                    else f"{desc} — {random.choice(['Burger Bar', 'Sushi Place', 'Pizza Spot', 'Taco Stand', 'Salad Bowl'])}",
                    category=cat,
                    subcategory=sub,
                    type="expense",
                    date=current,
                ))
            current += timedelta(days=1)

    # Occasional larger expenses
    large_expenses = [
        ("Car Insurance", 180.0, "Transportation", "Car Insurance"),
        ("Clothing Haul", 120.0, "Shopping", "Clothing"),
        ("Dentist Visit", 150.0, "Healthcare", "Dental"),
        ("Haircut", 45.0, "Personal Care", "Haircut"),
        ("Movie Night", 25.0, "Entertainment", "Movies"),
        ("Concert Tickets", 85.0, "Entertainment", "Concerts"),
        ("Home Supplies", 55.0, "Shopping", "Home Goods"),
        ("Steam Games", 35.0, "Entertainment", "Games"),
        ("Domain Renewal", 14.99, "Subscriptions", "Domain Renewal"),
        ("Textbook", 89.0, "Education", "Books"),
    ]
    for desc, amt, cat, sub in large_expenses:
        d = start_date + timedelta(days=random.randint(1, 89))
        db.session.add(Transaction(
            amount=amt,
            description=desc,
            category=cat,
            subcategory=sub,
            type="expense",
            date=d,
        ))

    db.session.commit()


# ---------------------------------------------------------------------------
# Insights Engine
# ---------------------------------------------------------------------------

def compute_velocity(transactions):
    """
    Compare current week's average daily spending vs trailing 3-month average.
    Returns dict with velocity metrics and an alert flag.
    """
    today = date.today()
    # Current week (last 7 days)
    week_ago = today - timedelta(days=7)
    # Trailing period (last 90 days, excluding current week)
    three_months_ago = today - timedelta(days=90)

    current_week_txns = [
        t for t in transactions
        if t["type"] == "expense" and three_months_ago <= t["_date"] <= today
    ]

    # Actually let me use the date objects properly
    current_week = [t for t in transactions if t["type"] == "expense" and week_ago < t["_date"] <= today]
    trailing = [t for t in transactions if t["type"] == "expense" and three_months_ago < t["_date"] <= week_ago]

    current_avg = sum(t["amount"] for t in current_week) / max(1, len(set(t["_date"] for t in current_week)))
    trailing_avg = sum(t["amount"] for t in trailing) / max(1, len(set(t["_date"] for t in trailing)))

    if trailing_avg == 0:
        return {"current_avg": round(current_avg, 2), "normal_avg": 0, "is_elevated": False, "percentage": 0}

    ratio = (current_avg / trailing_avg) if trailing_avg > 0 else 1
    is_elevated = ratio > 1.3  # 30% above normal triggers alert

    return {
        "current_avg": round(current_avg, 2),
        "normal_avg": round(trailing_avg, 2),
        "is_elevated": is_elevated,
        "percentage": round((ratio - 1) * 100, 1),
    }


def compute_runway(balance, transactions):
    """
    Calculate days of runway based on current balance and average daily expense burn rate.
    """
    today = date.today()
    three_months_ago = today - timedelta(days=90)

    expenses = [t for t in transactions if t["type"] == "expense" and t["_date"] >= three_months_ago]
    if not expenses:
        return {"days": None, "balance": balance, "daily_burn": 0, "status": "unknown"}

    total_burn = sum(t["amount"] for t in expenses)
    days_span = max(1, (today - three_months_ago).days)
    daily_burn = total_burn / days_span

    if daily_burn <= 0:
        return {"days": None, "balance": balance, "daily_burn": 0, "status": "no_expenses"}

    days = int(balance / daily_burn)

    if days > 365:
        status = "healthy"
    elif days > 60:
        status = "good"
    elif days > 30:
        status = "warning"
    else:
        status = "critical"

    return {
        "days": days,
        "balance": round(balance, 2),
        "daily_burn": round(daily_burn, 2),
        "status": status,
    }


def detect_anomalies(transactions):
    """
    Find categories where current week spending deviates significantly from normal.
    Uses a simple standard-deviation-based approach.
    """
    today = date.today()
    week_ago = today - timedelta(days=7)
    four_weeks_ago = today - timedelta(days=28)

    # Group by category for current week vs trailing 4 weeks
    current_by_cat = defaultdict(float)
    trailing_by_cat = defaultdict(list)

    for t in transactions:
        if t["type"] != "expense":
            continue
        if week_ago < t["_date"] <= today:
            current_by_cat[t["category"]] += t["amount"]
        elif four_weeks_ago <= t["_date"] <= week_ago:
            trailing_by_cat[t["category"]].append(t["amount"])

    anomalies = []
    for cat, current_total in current_by_cat.items():
        amounts = trailing_by_cat.get(cat, [])
        if len(amounts) < 2:
            continue

        # Weekly average in trailing period
        weekly_avg = sum(amounts) / max(1, len(amounts))
        # We want the normal weekly total, so let's compute per-week totals
        # Since we have 4 weeks, group by week
        weekly_totals = []
        for w in range(4):
            w_start = four_weeks_ago + timedelta(weeks=w)
            w_end = w_start + timedelta(days=7)
            week_sum = sum(
                t["amount"] for t in transactions
                if t["type"] == "expense"
                and t["category"] == cat
                and w_start <= t["_date"] < w_end
            )
            weekly_totals.append(week_sum)

        if len(weekly_totals) < 2:
            continue

        mean = statistics.mean(weekly_totals)
        stdev = statistics.stdev(weekly_totals) if len(weekly_totals) > 1 else mean * 0.3

        if mean == 0:
            continue

        deviation = (current_total - mean) / max(stdev, mean * 0.1)

        if abs(deviation) > 1.5:
            anomalies.append({
                "category": cat,
                "current_week": round(current_total, 2),
                "normal_weekly": round(mean, 2),
                "deviation": round(deviation, 1),
                "is_overspend": current_total > mean,
                "explanation": (
                    f"Spent ${current_total:.0f} on {cat} this week "
                    f"({'+' if current_total > mean else ''}${current_total - mean:.0f} "
                    f"vs your typical ${mean:.0f})"
                ),
            })

    return sorted(anomalies, key=lambda x: abs(x["deviation"]), reverse=True)


def detect_recurring(transactions):
    """
    Find transactions that appear monthly (same description, similar amount).
    """
    today = date.today()
    three_months_ago = today - timedelta(days=90)

    # Group by (description, rounded amount)
    groups = defaultdict(list)
    for t in transactions:
        if t["type"] == "expense" and t["_date"] >= three_months_ago:
            key = (t["description"], round(t["amount"] * 2) / 2)  # Round to nearest $0.50
            groups[key].append(t)

    recurring = []
    for (desc, amt), txns in groups.items():
        if len(txns) >= 2:
            # Check if they appear in different months
            months_seen = set((t["_date"].year, t["_date"].month) for t in txns)
            if len(months_seen) >= 2:
                recurring.append({
                    "description": desc,
                    "amount": round(amt, 2),
                    "frequency": "monthly",
                    "months_seen": len(months_seen),
                    "total_spent": round(sum(t["amount"] for t in txns), 2),
                    "category": txns[0]["category"],
                })

    return sorted(recurring, key=lambda x: x["total_spent"], reverse=True)[:10]


def detect_dark_patterns(transactions):
    """
    Identify subscriptions the user might have forgotten about.
    Criteria: recurring monthly charge, subscription category, low engagement.
    """
    recurring = detect_recurring(transactions)

    dark_patterns = []
    for r in recurring:
        # Subscription category or small amounts that fly under radar
        if r["category"] in ("Subscriptions", "Entertainment", "Other"):
            # Check how long it's been running
            dark_patterns.append({
                "description": r["description"],
                "amount": r["amount"],
                "monthly_cost": r["amount"],
                "total_spent": r["total_spent"],
                "months_active": r["months_seen"],
                "risk_level": "high" if r["amount"] < 20 else "medium",
                "reason": (
                    f"${r['amount']:.2f}/mo for {r['description']} — "
                    f"${r['total_spent']:.2f} spent over {r['months_seen']} months"
                ),
            })

    return dark_patterns


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/api/transactions", methods=["GET"])
def get_transactions():
    """List transactions with filtering and pagination."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    category = request.args.get("category")
    txn_type = request.args.get("type")
    month = request.args.get("month", type=int)
    year = request.args.get("year", type=int)
    search = request.args.get("search")

    query = Transaction.query.order_by(Transaction.date.desc())

    if category:
        query = query.filter(Transaction.category == category)
    if txn_type:
        query = query.filter(Transaction.type == txn_type)
    if month and year:
        query = query.filter(
            db.extract("month", Transaction.date) == month,
            db.extract("year", Transaction.date) == year,
        )
    elif month:
        query = query.filter(db.extract("month", Transaction.date) == month)
    elif year:
        query = query.filter(db.extract("year", Transaction.date) == year)
    if search:
        query = query.filter(Transaction.description.ilike(f"%{search}%"))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "transactions": [t.to_dict() for t in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "page": page,
        "per_page": per_page,
    })


@app.route("/api/transactions", methods=["POST"])
def create_transaction():
    """Create a new transaction."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    required = ["amount", "description", "category", "type", "date"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    if data["type"] not in ("income", "expense"):
        return jsonify({"error": "Type must be 'income' or 'expense'"}), 400

    try:
        txn_date = date.fromisoformat(data["date"])
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid date format (use YYYY-MM-DD)"}), 400

    txn = Transaction(
        amount=float(data["amount"]),
        description=data["description"],
        category=data["category"],
        subcategory=data.get("subcategory"),
        type=data["type"],
        date=txn_date,
    )
    db.session.add(txn)
    db.session.commit()

    return jsonify(txn.to_dict()), 201


@app.route("/api/transactions/<int:txn_id>", methods=["DELETE"])
def delete_transaction(txn_id):
    """Delete a transaction."""
    txn = db.session.get(Transaction, txn_id)
    if not txn:
        return jsonify({"error": "Transaction not found"}), 404

    db.session.delete(txn)
    db.session.commit()
    return jsonify({"message": "Deleted"}), 200


@app.route("/api/summary", methods=["GET"])
def get_summary():
    """Return aggregated financial summary for a given month/year."""
    today = date.today()
    month = request.args.get("month", today.month, type=int)
    year = request.args.get("year", today.year, type=int)

    transactions = Transaction.query.all()

    # Filter to selected month
    monthly_txns = [
        t for t in transactions
        if t.date.month == month and t.date.year == year
    ]

    total_income = sum(t.amount for t in monthly_txns if t.type == "income")
    total_expenses = sum(t.amount for t in monthly_txns if t.type == "expense")
    net = total_income - total_expenses

    # Category breakdown (expenses only)
    category_breakdown = defaultdict(float)
    for t in monthly_txns:
        if t.type == "expense":
            category_breakdown[t.category] += t.amount

    # All-time balance (sum of all transactions)
    all_income = sum(t.amount for t in transactions if t.type == "income")
    all_expenses = sum(t.amount for t in transactions if t.type == "expense")
    balance = round(all_income - all_expenses, 2)

    # Monthly trends (last 6 months)
    trends = []
    for i in range(5, -1, -1):
        m = month - i
        y = year
        while m <= 0:
            m += 12
            y -= 1
        while m > 12:
            m -= 12
            y += 1

        m_txns = [t for t in transactions if t.date.month == m and t.date.year == y]
        m_income = sum(t.amount for t in m_txns if t.type == "income")
        m_expenses = sum(t.amount for t in m_txns if t.type == "expense")
        trends.append({
            "month": m,
            "year": y,
            "income": round(m_income, 2),
            "expenses": round(m_expenses, 2),
            "net": round(m_income - m_expenses, 2),
        })

    return jsonify({
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "net": round(net, 2),
        "balance": balance,
        "transaction_count": len(monthly_txns),
        "category_breakdown": [
            {"category": cat, "amount": round(amt, 2)}
            for cat, amt in sorted(category_breakdown.items(), key=lambda x: -x[1])
        ],
        "monthly_trends": trends,
    })


@app.route("/api/insights", methods=["GET"])
def get_insights():
    """Return computed insights: velocity, runway, anomalies, recurring, dark patterns."""
    transactions_raw = Transaction.query.all()
    # Convert to dicts and add date parsers for insights engine
    txns = []
    for t in transactions_raw:
        d = t.to_dict()
        d["_date"] = t.date
        txns.append(d)

    today = date.today()

    # Balance
    total_income = sum(t.amount for t in transactions_raw if t.type == "income")
    total_expenses = sum(t.amount for t in transactions_raw if t.type == "expense")
    balance = total_income - total_expenses

    velocity = compute_velocity(txns)
    runway = compute_runway(balance, txns)
    anomalies = detect_anomalies(txns)
    recurring = detect_recurring(txns)
    dark_patterns = detect_dark_patterns(txns)

    return jsonify({
        "velocity": velocity,
        "runway": runway,
        "anomalies": anomalies,
        "recurring": recurring[:8],
        "dark_patterns": dark_patterns,
    })


@app.route("/api/budgets", methods=["GET"])
def get_budgets():
    """List budgets, optionally filtered by month/year."""
    month = request.args.get("month", type=int)
    year = request.args.get("year", type=int)

    query = Budget.query
    if month:
        query = query.filter(Budget.month == month)
    if year:
        query = query.filter(Budget.year == year)

    budgets = query.all()

    # Compute spending per category for budget vs actual comparison
    today = date.today()
    current_month = month or today.month
    current_year = year or today.year

    transactions = Transaction.query.filter(
        db.extract("month", Transaction.date) == current_month,
        db.extract("year", Transaction.date) == current_year,
        Transaction.type == "expense",
    ).all()

    spent_by_cat = defaultdict(float)
    for t in transactions:
        spent_by_cat[t.category] += t.amount

    result = []
    for b in budgets:
        spent = round(spent_by_cat.get(b.category, 0), 2)
        result.append({
            **b.to_dict(),
            "spent": spent,
            "remaining": round(b.amount - spent, 2),
            "percentage": round((spent / b.amount) * 100, 1) if b.amount > 0 else 0,
        })

    return jsonify(result)


@app.route("/api/budgets", methods=["POST"])
def create_budget():
    """Create a new budget entry."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    required = ["category", "amount", "month", "year"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    budget = Budget(
        category=data["category"],
        amount=float(data["amount"]),
        month=int(data["month"]),
        year=int(data["year"]),
    )
    db.session.add(budget)
    db.session.commit()
    return jsonify(budget.to_dict()), 201


@app.route("/api/budgets/<int:budget_id>", methods=["PUT"])
def update_budget(budget_id):
    """Update a budget entry."""
    budget = db.session.get(Budget, budget_id)
    if not budget:
        return jsonify({"error": "Budget not found"}), 404

    data = request.get_json()
    if "amount" in data:
        budget.amount = float(data["amount"])
    db.session.commit()
    return jsonify(budget.to_dict())


@app.route("/api/budgets/<int:budget_id>", methods=["DELETE"])
def delete_budget(budget_id):
    """Delete a budget entry."""
    budget = db.session.get(Budget, budget_id)
    if not budget:
        return jsonify({"error": "Budget not found"}), 404
    db.session.delete(budget)
    db.session.commit()
    return jsonify({"message": "Deleted"}), 200


@app.route("/api/categories", methods=["GET"])
def get_categories():
    """Return the list of categories."""
    return jsonify({
        "categories": CATEGORIES,
        "subcategories": SUBCATEGORIES,
    })


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()})


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_database()
    print("⚡ Finance Dashboard API running on http://localhost:5000")
    app.run(debug=True, port=5000)
