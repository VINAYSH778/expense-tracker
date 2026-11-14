import streamlit as st
import streamlit.components.v1 as components

from datetime import date
from calendar import month_name
from html import escape
from io import BytesIO

from storage import (
    initialize_files,
    get_incomes,
    get_expenses,
    get_budget,
    add_income,
    add_expense,
    set_monthly_budget
)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

initialize_files()

TODAY = date.today()
MONTH_KEY = TODAY.strftime("%Y-%m")


# =========================================================
# GLOBAL CSS
# =========================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg: #0b1020;
    --sidebar: #101827;
    --card: #151f32;
    --card2: #19263b;
    --border: #293850;
    --text: #f1f5f9;
    --muted: #94a3b8;
    --purple: #8b5cf6;
    --green: #22c55e;
    --red: #f05268;
    --blue: #6366f1;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background: var(--bg) !important;
    color: var(--text);
}

/* Top white header fix */
header[data-testid="stHeader"] {
    background: var(--bg) !important;
    border: none !important;
}

[data-testid="stToolbar"] {
    background: var(--bg) !important;
}

[data-testid="stDecoration"] {
    display: none !important;
}

/* Main content */
.block-container {
    max-width: 1500px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

h1, h2, h3, h4 {
    color: var(--text) !important;
    font-weight: 700 !important;
}

p, label {
    color: #cbd5e1;
}

small {
    color: var(--muted);
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: var(--sidebar) !important;
    border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] > div:first-child {
    background: var(--sidebar) !important;
}

[data-testid="stSidebar"] .block-container {
    padding: 1.4rem 1rem;
}

.sidebar-brand {
    font-size: 22px;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 3px;
}

.sidebar-subtitle {
    color: var(--muted);
    font-size: 12px;
    margin-bottom: 22px;
}

/* Sidebar navigation: full width underline */
[data-testid="stSidebar"] .stButton {
    margin: 0 !important;
}

[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    min-height: 48px;
    padding: 12px 9px !important;
    text-align: left !important;
    justify-content: flex-start !important;
    border: none !important;
    border-bottom: 1px solid #2a3850 !important;
    border-radius: 0 !important;
    background: transparent !important;
    color: #cbd5e1 !important;
    font-weight: 600;
    box-shadow: none !important;
    transition: 0.2s ease;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background: #1a2940 !important;
    color: white !important;
    border-bottom-color: var(--purple) !important;
}

[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: #1a2940 !important;
    color: #c4b5fd !important;
    border-bottom: 2px solid var(--purple) !important;
}

/* Form controls */
input, textarea {
    background: #151f32 !important;
    color: white !important;
    border-color: #34445f !important;
}

[data-baseweb="select"] > div {
    background: #151f32 !important;
    border-color: #34445f !important;
    color: white !important;
}

[data-testid="stDateInput"] input {
    background: #151f32 !important;
    color: white !important;
}

[data-testid="stForm"] {
    background: #111b2d;
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 20px;
}

/* Normal buttons */
.stButton > button,
.stDownloadButton > button,
.stFormSubmitButton > button {
    border-radius: 9px !important;
    font-weight: 600 !important;
}

.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"] {
    background: var(--purple) !important;
    border: 1px solid var(--purple) !important;
    color: white !important;
}

/* Metrics */
[data-testid="stMetric"] {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 13px;
    padding: 16px;
}

[data-testid="stMetricLabel"] {
    color: var(--muted) !important;
}

[data-testid="stMetricValue"] {
    color: white !important;
    font-size: 1.5rem !important;
}

/* Progress bar */
[data-testid="stProgressBar"] > div {
    background: #293850;
}

/* Dividers */
hr {
    border-color: var(--border) !important;
}

/* Captions */
[data-testid="stCaptionContainer"] {
    color: var(--muted);
}

/* Tables */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border);
    border-radius: 12px;
}

/* Mobile spacing */
@media (max-width: 768px) {
    .block-container {
        padding: 1rem 0.8rem 2rem;
    }
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# COMMON HELPERS
# =========================================================

def money(value):
    return f"₹{float(value):,.0f}"


def amount_of(item):
    try:
        return max(0.0, float(item.get("amount", 0)))
    except (ValueError, TypeError, AttributeError):
        return 0.0


def current_month_items(items):
    return [
        item for item in items
        if str(item.get("date", "")).startswith(MONTH_KEY)
    ]


def total_amount(items):
    return sum(amount_of(item) for item in items)


def monthly_total(items, year, month):
    key = f"{year}-{month:02d}"
    return sum(
        amount_of(item)
        for item in items
        if str(item.get("date", "")).startswith(key)
    )


def page_title(title, subtitle):
    st.title(title)
    st.caption(subtitle)


def html_card(title, body, height=340):
    """Render chart panel and its SVG in a single HTML iframe."""
    document = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            padding: 0;
            background: transparent;
            color: #f1f5f9;
            font-family: Arial, sans-serif;
        }}
        .card {{
            width: 100%;
            padding: 18px 16px;
            background: #151f32;
            border: 1px solid #293850;
            border-radius: 14px;
            overflow: hidden;
        }}
        .heading {{
            font-size: 16px;
            font-weight: 700;
            margin: 0 0 14px;
            color: #f8fafc;
        }}
        svg {{
            width: 100%;
            height: auto;
            display: block;
        }}
    </style>
    </head>
    <body>
        <div class="card">
            <div class="heading">{escape(title)}</div>
            {body}
        </div>
    </body>
    </html>
    """

    components.html(
        document,
        height=height,
        scrolling=False
    )


def kpi_card(title, value, subtitle="", accent="#8b5cf6", icon=""):
    document = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            background: transparent;
            font-family: Arial, sans-serif;
        }}
        .card {{
            min-height: 112px;
            padding: 17px;
            border-radius: 13px;
            background: #151f32;
            border: 1px solid #293850;
            border-top: 3px solid {accent};
            color: white;
        }}
        .label {{
            color: #a5b4c8;
            font-size: 12px;
            margin-bottom: 10px;
        }}
        .value {{
            color: #f8fafc;
            font-size: 23px;
            font-weight: 700;
            overflow-wrap: anywhere;
        }}
        .subtitle {{
            color: #94a3b8;
            font-size: 11px;
            margin-top: 6px;
        }}
    </style>
    </head>
    <body>
        <div class="card">
            <div class="label">{icon} {escape(title)}</div>
            <div class="value">{escape(str(value))}</div>
            <div class="subtitle">{escape(subtitle)}</div>
        </div>
    </body>
    </html>
    """

    components.html(document, height=125, scrolling=False)


# =========================================================
# SVG CHARTS
# =========================================================

def line_chart(values, labels, color="#f05268"):
    width = 720
    height = 260
    left, right, top, bottom = 62, 18, 20, 42

    plot_width = width - left - right
    plot_height = height - top - bottom

    maximum = max(values, default=0)
    maximum = maximum * 1.15 if maximum > 0 else 100

    points = []

    for index, value in enumerate(values):
        x = left + plot_width * index / max(len(values) - 1, 1)
        y = top + plot_height - (value / maximum * plot_height)
        points.append((x, y))

    point_string = " ".join(
        f"{x:.1f},{y:.1f}" for x, y in points
    )

    grid = ""

    for i in range(5):
        y = top + plot_height * i / 4
        amount = maximum * (4 - i) / 4

        grid += f"""
        <line x1="{left}" y1="{y}" x2="{width-right}" y2="{y}"
              stroke="#334155" stroke-width="1"/>
        <text x="{left-8}" y="{y+4}" text-anchor="end"
              fill="#94a3b8" font-size="10">
              {amount / 1000:.0f}k
        </text>
        """

    circles = ""
    xlabels = ""

    for (x, y), label, value in zip(points, labels, values):
        circles += f"""
        <circle cx="{x}" cy="{y}" r="4.5"
                fill="{color}" stroke="#151f32" stroke-width="2">
            <title>{escape(label)}: ₹{value:,.2f}</title>
        </circle>
        """

        xlabels += f"""
        <text x="{x}" y="{height-14}" text-anchor="middle"
              fill="#94a3b8" font-size="10">{escape(label)}</text>
        """

    return f"""
    <svg viewBox="0 0 {width} {height}"
         xmlns="http://www.w3.org/2000/svg">
        {grid}
        <polyline points="{point_string}" fill="none"
                  stroke="{color}" stroke-width="3"
                  stroke-linecap="round" stroke-linejoin="round"/>
        {circles}
        {xlabels}
    </svg>
    """


def area_chart(values, labels, color="#6366f1"):
    width = 720
    height = 260
    left, right, top, bottom = 62, 18, 20, 42

    plot_width = width - left - right
    plot_height = height - top - bottom

    maximum = max(values, default=0)
    maximum = maximum * 1.15 if maximum > 0 else 100

    points = []

    for index, value in enumerate(values):
        x = left + plot_width * index / max(len(values) - 1, 1)
        y = top + plot_height - (value / maximum * plot_height)
        points.append((x, y))

    line_points = " ".join(
        f"{x:.1f},{y:.1f}" for x, y in points
    )

    area_points = (
        f"{left},{top + plot_height} "
        + line_points
        + f" {width-right},{top + plot_height}"
    )

    grid = ""

    for i in range(5):
        y = top + plot_height * i / 4
        amount = maximum * (4 - i) / 4

        grid += f"""
        <line x1="{left}" y1="{y}" x2="{width-right}" y2="{y}"
              stroke="#334155" stroke-width="1"/>
        <text x="{left-8}" y="{y+4}" text-anchor="end"
              fill="#94a3b8" font-size="10">
              {amount / 1000:.0f}k
        </text>
        """

    xlabels = ""

    for index, label in enumerate(labels):
        x = left + plot_width * index / max(len(labels) - 1, 1)

        xlabels += f"""
        <text x="{x}" y="{height-14}" text-anchor="middle"
              fill="#94a3b8" font-size="10">{escape(label)}</text>
        """

    return f"""
    <svg viewBox="0 0 {width} {height}"
         xmlns="http://www.w3.org/2000/svg">
        {grid}
        <polygon points="{area_points}"
                 fill="{color}" opacity="0.22"/>
        <polyline points="{line_points}"
                  fill="none" stroke="{color}" stroke-width="2.5"/>
        {xlabels}
    </svg>
    """


def horizontal_bar_chart(data, color="#6366f1"):
    if not data:
        return """
        <div style="height:150px;display:flex;align-items:center;
        justify-content:center;color:#94a3b8;font-size:13px">
            No expense data available for this year.
        </div>
        """

    width = 720
    label_width = 190
    value_width = 110
    bar_width = width - label_width - value_width
    row_height = 44
    height = max(100, len(data) * row_height + 15)

    maximum = max((value for _, value in data), default=0)
    maximum = maximum if maximum > 0 else 1

    bars = ""

    for index, (label, value) in enumerate(data):
        y = index * row_height + 8
        current_width = value / maximum * bar_width
        short_label = escape(str(label)[:25])

        bars += f"""
        <text x="{label_width-12}" y="{y+19}" text-anchor="end"
              fill="#cbd5e1" font-size="12">{short_label}</text>
        <rect x="{label_width}" y="{y+5}" width="{bar_width}"
              height="20" rx="5" fill="#293850"/>
        <rect x="{label_width}" y="{y+5}" width="{current_width:.1f}"
              height="20" rx="5" fill="{color}"/>
        <text x="{label_width+current_width+8}" y="{y+20}"
              fill="#f8fafc" font-size="11" font-weight="600">
              ₹{value:,.0f}
        </text>
        """

    return f"""
    <svg viewBox="0 0 {width} {height}"
         xmlns="http://www.w3.org/2000/svg">
        {bars}
    </svg>
    """


def donut_chart(percentage):
    percentage = max(0, min(float(percentage), 100))
    circumference = 2 * 3.14159265 * 65
    offset = circumference * (1 - percentage / 100)

    return f"""
    <svg viewBox="0 0 180 180"
         xmlns="http://www.w3.org/2000/svg"
         style="width:100%;max-width:180px;display:block;margin:auto">
        <circle cx="90" cy="90" r="65"
                fill="none" stroke="#293850" stroke-width="17"/>
        <circle cx="90" cy="90" r="65"
                fill="none" stroke="#6366f1" stroke-width="17"
                stroke-linecap="round"
                stroke-dasharray="{circumference}"
                stroke-dashoffset="{offset}"
                transform="rotate(-90 90 90)"/>
        <text x="90" y="85" text-anchor="middle"
              fill="#ffffff" font-size="27" font-weight="700">
              {percentage:.0f}%
        </text>
        <text x="90" y="106" text-anchor="middle"
              fill="#94a3b8" font-size="11">
              Budget Spent
        </text>
    </svg>
    """


def donut_panel(percentage):
    document = f"""
    <html>
    <head>
    <style>
        body {{
            margin: 0;
            background: transparent;
            font-family: Arial, sans-serif;
        }}
        .card {{
            height: 125px;
            background: #151f32;
            border: 1px solid #293850;
            border-radius: 13px;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 4px;
        }}
        svg {{
            width: 115px;
            height: 115px;
        }}
    </style>
    </head>
    <body>
        <div class="card">{donut_chart(percentage)}</div>
    </body>
    </html>
    """

    components.html(document, height=130, scrolling=False)


# =========================================================
# PDF REPORT
# =========================================================

def create_daily_pdf(selected_date, transactions):
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle
        )
        from reportlab.lib.units import mm

    except ImportError:
        st.error("ReportLab install karo: uv add reportlab")
        return None

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm
    )

    styles = getSampleStyleSheet()
    story = [
        Paragraph("Daily Expense Report", styles["Title"]),
        Spacer(1, 10),
        Paragraph(f"Date: {selected_date}", styles["Normal"]),
        Spacer(1, 15)
    ]

    rows = [["Category", "Description", "Amount", "Type"]]
    total = 0

    for item in transactions:
        amount = amount_of(item)
        total += amount

        rows.append([
            str(item.get("category", "Other"))[:30],
            str(item.get("description", ""))[:45],
            f"Rs. {amount:,.2f}",
            "Unnecessary" if item.get("unnecessary") else "Necessary"
        ])

    rows.append(["", "Total", f"Rs. {total:,.2f}", ""])

    table = Table(
        rows,
        colWidths=[38 * mm, 65 * mm, 35 * mm, 38 * mm],
        repeatRows=1
    )

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#312e81")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 7),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e0e7ff")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold")
    ]))

    story.append(table)
    doc.build(story)

    buffer.seek(0)
    return buffer


# =========================================================
# LOAD DATA
# =========================================================

incomes = get_incomes()
expenses = get_expenses()
budget = get_budget()

month_incomes = current_month_items(incomes)
month_expenses = current_month_items(expenses)

monthly_income = total_amount(month_incomes)
monthly_expense = total_amount(month_expenses)
balance = monthly_income - monthly_expense
remaining_budget = budget - monthly_expense

budget_percentage = (
    monthly_expense / budget * 100 if budget > 0 else 0
)


# =========================================================
# SIDEBAR NAVIGATION
# =========================================================

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

with st.sidebar:
    st.markdown(
        '<div class="sidebar-brand">💰 Expense Tracker</div>'
        '<div class="sidebar-subtitle">Personal Finance Manager</div>',
        unsafe_allow_html=True
    )

    st.divider()

    navigation = [
        ("Dashboard", "🏠"),
        ("Add Income", "💵"),
        ("Add Expense", "💸"),
        ("Set Budget", "🎯"),
        ("Analysis", "📊"),
        ("Manage Money", "📁")
    ]

    for name, icon in navigation:
        active = st.session_state.page == name

        if st.button(
            f"{icon}   {name}",
            key=f"nav_{name}",
            type="primary" if active else "secondary"
        ):
            st.session_state.page = name
            st.rerun()

    st.divider()

    st.markdown(
        '<div class="sidebar-subtitle">🌙 Dark theme enabled</div>',
        unsafe_allow_html=True
    )


# =========================================================
# DASHBOARD
# =========================================================

if st.session_state.page == "Dashboard":

    page_title(
        "Welcome to your Dashboard 👋",
        "Here is your current financial overview."
    )

    a, b, c, d = st.columns(4)

    with a:
        kpi_card("Total Balance", money(balance), "Income minus expenses", "#8b5cf6", "💰")
    with b:
        kpi_card("Monthly Income", money(monthly_income), "Income this month", "#22c55e", "↗")
    with c:
        kpi_card("Monthly Expenses", money(monthly_expense), "Expenses this month", "#f05268", "↘")
    with d:
        kpi_card("Monthly Budget", money(budget), "Your spending limit", "#6366f1", "🎯")

    st.markdown("### Recent Transactions")

    recent = []

    for item in incomes:
        recent.append({
            "type": "Income",
            "name": item.get("source", "Income"),
            "date": item.get("date", ""),
            "amount": amount_of(item)
        })

    for item in expenses:
        recent.append({
            "type": "Expense",
            "name": item.get("category", "Expense"),
            "date": item.get("date", ""),
            "amount": amount_of(item)
        })

    recent.sort(key=lambda x: str(x["date"]), reverse=True)

    if not recent:
        st.info("No transactions yet. Add your first income or expense.")

    for item in recent[:8]:
        sign = "+" if item["type"] == "Income" else "-"
        color = "#22c55e" if item["type"] == "Income" else "#f05268"

        st.html(f"""
        <div style="background:#151f32;border:1px solid #293850;
                    border-radius:11px;padding:14px;margin-bottom:9px;
                    display:flex;justify-content:space-between;gap:10px">
            <div>
                <div style="font-weight:700;color:#f8fafc">
                    {escape(str(item['name']))}
                </div>
                <div style="font-size:12px;color:#94a3b8">
                    {escape(str(item['type']))} · {escape(str(item['date']))}
                </div>
            </div>
            <div style="font-weight:700;color:{color}">
                {sign}{money(item['amount'])}
            </div>
        </div>
        """)


# =========================================================
# ADD INCOME
# =========================================================

elif st.session_state.page == "Add Income":

    page_title("💵 Add Income", "Record your income details.")

    with st.form("income_form", clear_on_submit=True):

        amount = st.number_input(
            "Income Amount (₹)",
            min_value=0.0,
            step=100.0
        )

        source = st.selectbox(
            "Income Source",
            [
                "Salary", "Freelancing", "Business",
                "Investment", "Gift", "Other"
            ]
        )

        income_date = st.date_input("Income Date", value=TODAY)
        description = st.text_area("Description")

        submitted = st.form_submit_button(
            "Save Income",
            type="primary"
        )

        if submitted:
            if amount <= 0:
                st.error("Amount 0 se zyada hona chahiye.")
            else:
                add_income(amount, source, income_date, description)
                st.success("Income successfully saved!")
                st.rerun()


# =========================================================
# ADD EXPENSE
# =========================================================

elif st.session_state.page == "Add Expense":

    page_title("💸 Add Expense", "Record your daily expenses.")

    with st.form("expense_form", clear_on_submit=True):

        amount = st.number_input(
            "Expense Amount (₹)",
            min_value=0.0,
            step=50.0
        )

        category = st.selectbox(
            "Expense Category",
            [
                "Food", "Travel", "Shopping", "Rent",
                "Bills", "Health", "Education",
                "Entertainment", "Other"
            ]
        )

        expense_date = st.date_input("Expense Date", value=TODAY)
        description = st.text_area("Description")

        unnecessary = st.checkbox(
            "This is an unnecessary expense"
        )

        submitted = st.form_submit_button(
            "Save Expense",
            type="primary"
        )

        if submitted:
            if amount <= 0:
                st.error("Amount 0 se zyada hona chahiye.")
            else:
                add_expense(
                    amount,
                    category,
                    expense_date,
                    description,
                    unnecessary
                )

                st.success("Expense successfully saved!")
                st.rerun()


# =========================================================
# SET BUDGET
# =========================================================

elif st.session_state.page == "Set Budget":

    page_title(
        "🎯 Set Monthly Budget",
        "Decide how much you want to spend each month."
    )

    kpi_card(
        "Current Monthly Budget",
        money(budget),
        "Your saved monthly limit",
        "#8b5cf6",
        "🎯"
    )

    st.write("")

    with st.form("budget_form"):

        new_budget = st.number_input(
            "Enter Monthly Budget (₹)",
            min_value=0.0,
            value=float(budget),
            step=500.0
        )

        submitted = st.form_submit_button(
            "Save Budget",
            type="primary"
        )

        if submitted:
            set_monthly_budget(new_budget)
            st.success("Monthly budget updated!")
            st.rerun()

    st.markdown("### Current Month Budget Status")

    if budget > 0:
        st.progress(min(budget_percentage / 100, 1.0))
        st.caption(f"{budget_percentage:.1f}% of budget used.")
    else:
        st.info("Set a budget to view your progress.")

    x, y = st.columns(2)
    x.metric("Spent", money(monthly_expense))
    y.metric("Remaining", money(remaining_budget))


# =========================================================
# ANALYSIS
# =========================================================

elif st.session_state.page == "Analysis":

    page_title(
        "📊 Budget Tracking Dashboard",
        "Understand your spending, budget usage and expense categories."
    )

    available_years = set()

    for item in expenses + incomes:
        value = str(item.get("date", ""))[:4]
        if value.isdigit():
            available_years.add(int(value))

    available_years.add(TODAY.year)
    available_years = sorted(available_years)

    selected_year = st.selectbox(
        "Select Year",
        available_years,
        index=available_years.index(TODAY.year)
    )

    year_expenses = [
        item for item in expenses
        if str(item.get("date", "")).startswith(str(selected_year))
    ]

    year_incomes = [
        item for item in incomes
        if str(item.get("date", "")).startswith(str(selected_year))
    ]

    year_total_expense = total_amount(year_expenses)
    year_total_income = total_amount(year_incomes)

    annual_budget = budget * 12
    annual_remaining = annual_budget - year_total_expense

    spent_percentage = (
        year_total_expense / annual_budget * 100
        if annual_budget > 0 else 0
    )

    remaining_percentage = max(0, 100 - spent_percentage)

    # Five KPI cards
    col1, col2, col3, col4, col5 = st.columns([1, 1, 0.9, 1, 1])

    with col1:
        kpi_card(
            "Annual Budget",
            money(annual_budget),
            "Monthly budget × 12",
            "#6366f1",
            "🎯"
        )

    with col2:
        kpi_card(
            "Total Expenses",
            money(year_total_expense),
            "Selected year",
            "#f05268",
            "💸"
        )

    with col3:
        donut_panel(spent_percentage)

    with col4:
        kpi_card(
            "Remaining Budget",
            money(annual_remaining),
            "Annual budget minus expenses",
            "#22c55e",
            "💰"
        )

    with col5:
        kpi_card(
            "% Remaining Budget",
            f"{remaining_percentage:.1f}%",
            "Budget still available",
            "#8b5cf6",
            "📊"
        )

    st.write("")

    # Monthly charts
    month_labels = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ]

    monthly_expenses = [
        monthly_total(year_expenses, selected_year, month)
        for month in range(1, 13)
    ]

    monthly_remaining = [
        max(0, budget - value)
        for value in monthly_expenses
    ]

    left, right = st.columns(2)

    with left:
        html_card(
            "📈 Monthly Project Expenses",
            line_chart(
                monthly_expenses,
                month_labels,
                "#f05268"
            ),
            height=320
        )

    with right:
        html_card(
            "💜 Remaining Budget by Month",
            area_chart(
                monthly_remaining,
                month_labels,
                "#6366f1"
            ),
            height=320
        )

    st.write("")

    # Category totals
    category_totals = {}

    for item in year_expenses:
        category = str(item.get("category", "Other"))
        category_totals[category] = (
            category_totals.get(category, 0) + amount_of(item)
        )

    category_data = sorted(
        category_totals.items(),
        key=lambda x: x[1],
        reverse=True
    )

    necessary_total = sum(
        amount_of(item)
        for item in year_expenses
        if not item.get("unnecessary", False)
    )

    unnecessary_total = sum(
        amount_of(item)
        for item in year_expenses
        if item.get("unnecessary", False)
    )

    left, right = st.columns(2)

    with left:
        html_card(
            "📂 Expense by Category",
            horizontal_bar_chart(category_data, "#6366f1"),
            height=max(230, min(450, 100 + len(category_data) * 44))
        )

    with right:
        html_card(
            "⚖️ Necessary vs Unnecessary",
            horizontal_bar_chart(
                [
                    ("Necessary Expenses", necessary_total),
                    ("Unnecessary Expenses", unnecessary_total)
                ],
                "#f05268"
            ),
            height=230
        )

    st.write("")

    # Summary
    st.markdown("### Yearly Summary")

    s1, s2, s3 = st.columns(3)

    s1.metric("Yearly Income", money(year_total_income))
    s2.metric("Yearly Expenses", money(year_total_expense))
    s3.metric(
        "Income - Expenses",
        money(year_total_income - year_total_expense)
    )

    st.caption(
        "Note: Annual budget is calculated using your currently saved "
        "monthly budget × 12. Historical budget changes are not stored."
    )


# =========================================================
# MANAGE MONEY
# =========================================================

elif st.session_state.page == "Manage Money":

    page_title(
        "📁 Manage Money",
        "Review your financial records and download reports."
    )

    st.markdown("### Monthly Overview")

    c1, c2, c3 = st.columns(3)

    c1.metric("Monthly Income", money(monthly_income))
    c2.metric("Monthly Expenses", money(monthly_expense))
    c3.metric("Monthly Difference", money(balance))

    st.markdown("### Budget Overview")

    b1, b2 = st.columns(2)

    b1.metric("Monthly Budget", money(budget))
    b2.metric("Budget Remaining", money(remaining_budget))

    if budget > 0:
        st.progress(min(budget_percentage / 100, 1.0))
        st.caption(f"{budget_percentage:.1f}% of monthly budget used.")
    else:
        st.info("Set a monthly budget to view budget progress.")

    st.divider()

    st.markdown("### 📄 Daily Expense PDF Report")

    selected_date = st.date_input(
        "Select Date for Report",
        value=TODAY,
        key="pdf_date"
    )

    selected_transactions = [
        item for item in expenses
        if str(item.get("date", "")) == str(selected_date)
    ]

    daily_total = total_amount(selected_transactions)

    r1, r2 = st.columns(2)

    r1.metric("Total Expenses", money(daily_total))
    r2.metric("Number of Transactions", len(selected_transactions))

    if selected_transactions:
        st.markdown("#### Transactions")

        for item in selected_transactions:
            st.write(
                f"**{item.get('category', 'Other')}** — "
                f"{money(amount_of(item))} — "
                f"{item.get('description', '')}"
            )

        pdf_file = create_daily_pdf(
            selected_date,
            selected_transactions
        )

        if pdf_file:
            st.download_button(
                "⬇️ Download Daily PDF",
                data=pdf_file,
                file_name=f"expense_report_{selected_date}.pdf",
                mime="application/pdf",
                type="primary"
            )

    else:
        st.info("No expenses found for this date.")

    st.divider()

    st.markdown("### All Expense Records")

    if expenses:
        sorted_expenses = sorted(
            expenses,
            key=lambda item: str(item.get("date", "")),
            reverse=True
        )

        for item in sorted_expenses:
            st.write(
                f"**{item.get('date', '')}** | "
                f"{item.get('category', 'Other')} | "
                f"{money(amount_of(item))}"
            )
    else:
        st.info("No expense records available.")