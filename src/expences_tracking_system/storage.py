import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

INCOME_FILE = DATA_DIR / "incomes.json"
EXPENSE_FILE = DATA_DIR / "expenses.json"
BUDGET_FILE = DATA_DIR / "budget.json"


def save_json(file_path, data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    temp_file = file_path.with_suffix(".tmp")

    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    temp_file.replace(file_path)


def load_json(file_path, default):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not file_path.exists():
        save_json(file_path, default)
        return default

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data if isinstance(data, type(default)) else default

    except (json.JSONDecodeError, OSError):
        return default


def initialize_files():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not INCOME_FILE.exists():
        save_json(INCOME_FILE, [])

    if not EXPENSE_FILE.exists():
        save_json(EXPENSE_FILE, [])

    if not BUDGET_FILE.exists():
        save_json(BUDGET_FILE, {"monthly_budget": 0})


def get_incomes():
    return load_json(INCOME_FILE, [])


def get_expenses():
    return load_json(EXPENSE_FILE, [])


def get_budget():
    data = load_json(BUDGET_FILE, {"monthly_budget": 0})

    try:
        return max(0.0, float(data.get("monthly_budget", 0)))
    except (ValueError, TypeError):
        return 0.0


def add_income(amount, source, income_date, description=""):
    incomes = get_incomes()

    incomes.append({
        "id": max([int(x.get("id", 0)) for x in incomes] or [0]) + 1,
        "amount": float(amount),
        "source": str(source),
        "date": str(income_date),
        "description": str(description)
    })

    save_json(INCOME_FILE, incomes)


def add_expense(
    amount,
    category,
    expense_date,
    description="",
    unnecessary=False
):
    expenses = get_expenses()

    expenses.append({
        "id": max([int(x.get("id", 0)) for x in expenses] or [0]) + 1,
        "amount": float(amount),
        "category": str(category),
        "date": str(expense_date),
        "description": str(description),
        "unnecessary": bool(unnecessary)
    })

    save_json(EXPENSE_FILE, expenses)


def set_monthly_budget(amount):
    save_json(BUDGET_FILE, {"monthly_budget": float(amount)})


def get_dashboard_data():
    incomes = get_incomes()
    expenses = get_expenses()
    budget = get_budget()

    from datetime import date

    month_key = date.today().strftime("%Y-%m")

    monthly_income = sum(
        float(item.get("amount", 0))
        for item in incomes
        if str(item.get("date", "")).startswith(month_key)
    )

    monthly_expenses = sum(
        float(item.get("amount", 0))
        for item in expenses
        if str(item.get("date", "")).startswith(month_key)
    )

    return {
        "incomes": incomes,
        "expenses": expenses,
        "budget": budget,
        "monthly_income": monthly_income,
        "monthly_expenses": monthly_expenses,
        "balance": monthly_income - monthly_expenses
    }